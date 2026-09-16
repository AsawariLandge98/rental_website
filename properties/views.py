from urllib.parse import quote

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import City
from dashboard.decorators import tenant_required
from reviews.models import Review
from visits.models import Visit
from .models import Property, SavedProperty


def get_city_options():
    """The admin-managed city list for the search/quick-search dropdown
    (core.City) — real, editable from /admin/dashboard/cms/cities/, not a
    hardcoded list. Property.city itself stays free text elsewhere, so an
    owner can still list in a city that isn't in this curated shortlist."""
    return list(City.objects.filter(is_active=True).values_list('name', flat=True))

BUDGET_OPTIONS = [
    ('0-15000', 'Under ₹15,000'),
    ('15000-30000', '₹15,000 - ₹30,000'),
    ('30000-50000', '₹30,000 - ₹50,000'),
    ('50000-100000', '₹50,000 - ₹1,00,000'),
    ('100000-', 'Above ₹1,00,000'),
]


def _property_card_context(property_obj, saved_ids=frozenset()):
    """Shapes a Property instance into the dict shape partials/property_card.html
    and property_detail.html already expect (built for the old dummy data)."""
    cover = property_obj.cover_photo
    amenities = list(property_obj.amenities.all())
    return {
        'id': property_obj.pk,
        'title': property_obj.title,
        'location': property_obj.display_location,
        'short_location': property_obj.short_location,
        'city': property_obj.city,
        'beds': property_obj.bedrooms or 0,
        'baths': property_obj.bathrooms or 0,
        'area': property_obj.total_area or 0,
        'floor_label': property_obj.floor_label,
        'furnishing': property_obj.get_furnishing_status_display() if property_obj.furnishing_status else '',
        'parking': property_obj.get_parking_display() if property_obj.parking else '',
        'amenities': amenities[:6],
        'amenities_more': max(len(amenities) - 6, 0),
        # Hotel/Guest House/Homestay listings are priced per night, not per
        # month — real, wizard-collected nightly_rate, previously never
        # actually consumed anywhere (every card/detail page silently
        # showed monthly_rent labeled "/month" even for these).
        'price': (property_obj.nightly_rate or 0) if property_obj.is_bookable else (property_obj.monthly_rent or 0),
        'price_period': 'night' if property_obj.is_bookable else 'month',
        'is_bookable': property_obj.is_bookable,
        'badge': property_obj.badge,
        'no_brokerage': property_obj.no_brokerage,
        'image': cover.image.url if cover else '',
        'is_saved': property_obj.pk in saved_ids,
        'photo_count': len(property_obj.photos.all()),
        # Only real when the queryset was annotated with these two (see
        # `_with_rating()` below) — never fabricated. getattr defaults to
        # None/0 so callers that pass an un-annotated instance (e.g. a
        # single property_detail() lookup, which computes its own separate
        # real review_average already) don't crash; the card template
        # treats a None rating as "no reviews yet" and hides the badge.
        'rating': getattr(property_obj, 'avg_rating', None),
        'review_count': getattr(property_obj, 'review_count', 0),
    }


def _with_rating(queryset):
    """Attaches a real average rating + review count to a Property queryset
    in one query (Avg/Count over the real reviews.Review relation) — used
    everywhere a grid of property cards is rendered, so the rating badge
    never costs an extra query per card (the N+1 this was deliberately
    deferred to avoid back in Feature 23)."""
    return queryset.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews', distinct=True))


def _saved_ids_for(user):
    if not user.is_authenticated:
        return frozenset()
    return frozenset(SavedProperty.objects.filter(tenant=user).values_list('property_id', flat=True))


def _phone_digits(mobile_number):
    """Normalizes a stored mobile number into bare digits for tel:/wa.me
    links, assuming a 10-digit number is an Indian number missing its
    country code."""
    digits = ''.join(ch for ch in mobile_number if ch.isdigit())
    if len(digits) == 10:
        digits = '91' + digits
    return digits


def _owner_contact_options(property_obj):
    """Real Call / WhatsApp / Email links for the owner — visible directly,
    with no inquiry-approval step (there's no Inquiries feature built yet,
    and the owner explicitly asked for contact details to be visible
    without one). Only shows the channels the owner opted into; if they
    didn't pick any, falls back to offering all three."""
    owner_user = property_obj.owner
    prefs = property_obj.contact_preferences or ['call', 'whatsapp', 'email']
    options = []

    if 'call' in prefs and owner_user.mobile_number:
        digits = _phone_digits(owner_user.mobile_number)
        options.append({
            'type': 'call', 'icon': 'phone', 'label': 'Call',
            'sublabel': owner_user.mobile_number, 'href': f'tel:+{digits}',
        })
    if 'whatsapp' in prefs and owner_user.mobile_number:
        digits = _phone_digits(owner_user.mobile_number)
        message = quote(f"Hi, I'm interested in your property \"{property_obj.title}\" on Rentora.")
        options.append({
            'type': 'whatsapp', 'icon': 'whatsapp', 'label': 'WhatsApp',
            'sublabel': 'Chat instantly', 'href': f'https://wa.me/{digits}?text={message}',
        })
    if 'email' in prefs and owner_user.email:
        options.append({
            'type': 'email', 'icon': 'envelope', 'label': 'Email',
            'sublabel': owner_user.email, 'href': f'mailto:{owner_user.email}',
        })
    return options


PRICE_SLIDER_MIN = 0
PRICE_SLIDER_MAX = 100000

BEDROOM_OPTIONS = [
    ('studio', '1 RK / Studio'),
    ('1', '1 BHK'),
    ('2', '2 BHK'),
    ('3', '3 BHK'),
    ('4plus', '4+ BHK'),
]


def search_results(request):
    queryset = _with_rating(
        Property.objects.filter(status=Property.Status.PUBLISHED).prefetch_related('photos', 'amenities'),
    )

    q = request.GET.get('q', '').strip()
    city = request.GET.get('city')
    area = request.GET.get('area')
    budget = request.GET.get('budget')
    property_types = [v for v in request.GET.getlist('property_type') if v]
    furnishing = [v for v in request.GET.getlist('furnishing') if v]
    bedrooms = [v for v in request.GET.getlist('bedrooms') if v]
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(city__icontains=q) | Q(area_locality__icontains=q) | Q(landmark__icontains=q)
        )
    if city:
        queryset = queryset.filter(city__iexact=city)
    if area:
        queryset = queryset.filter(area_locality__icontains=area)
    if property_types:
        queryset = queryset.filter(property_type__in=property_types)
    if budget:
        low, _, high = budget.partition('-')
        if low:
            queryset = queryset.filter(monthly_rent__gte=int(low))
        if high:
            queryset = queryset.filter(monthly_rent__lte=int(high))
    if price_min.isdigit() and int(price_min) > PRICE_SLIDER_MIN:
        queryset = queryset.filter(monthly_rent__gte=int(price_min))
    if price_max.isdigit() and int(price_max) < PRICE_SLIDER_MAX:
        queryset = queryset.filter(monthly_rent__lte=int(price_max))
    if furnishing:
        queryset = queryset.filter(furnishing_status__in=furnishing)
    if bedrooms:
        bedroom_filter = Q()
        for value in bedrooms:
            if value == 'studio':
                bedroom_filter |= Q(property_type=Property.PropertyType.STUDIO) | Q(bedrooms=0)
            elif value == '4plus':
                bedroom_filter |= Q(bedrooms__gte=4)
            elif value.isdigit():
                bedroom_filter |= Q(bedrooms=int(value))
        queryset = queryset.filter(bedroom_filter)

    sort = request.GET.get('sort', 'newest')
    sort_field = {'newest': '-created_at', 'price_asc': 'monthly_rent', 'price_desc': '-monthly_rent'}.get(sort, '-created_at')
    queryset = queryset.order_by(sort_field)

    per_page = request.GET.get('per_page', '12')
    per_page = per_page if per_page in ('12', '24', '48') else '12'
    paginator = Paginator(queryset, int(per_page))
    page_obj = paginator.get_page(request.GET.get('page'))

    saved_ids = _saved_ids_for(request.user)
    properties = [_property_card_context(p, saved_ids) for p in page_obj]

    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    context = {
        'properties': properties,
        'result_count': paginator.count,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'selected_per_page': per_page,
        'selected_sort': sort,
        'city_options': get_city_options(),
        'property_type_options': Property.PropertyType.choices,
        'budget_options': BUDGET_OPTIONS,
        'selected_q': q,
        'selected_city': city or '',
        'selected_area': area or '',
        'selected_property_types': property_types,
        'selected_budget': budget or '',
        'bedroom_options': BEDROOM_OPTIONS,
        'selected_bedrooms': bedrooms,
        'furnishing_options': Property.FurnishingStatus.choices,
        'selected_furnishing': furnishing,
        'selected_price_min': int(price_min) if price_min.isdigit() else PRICE_SLIDER_MIN,
        'selected_price_max': int(price_max) if price_max.isdigit() else PRICE_SLIDER_MAX,
        'price_slider_min': PRICE_SLIDER_MIN,
        'price_slider_max': PRICE_SLIDER_MAX,
    }
    return render(request, "properties/search_results.html", context)


def property_detail(request, pk):
    try:
        property_obj = Property.objects.prefetch_related('photos', 'amenities').get(
            pk=pk, status=Property.Status.PUBLISHED,
        )
    except Property.DoesNotExist:
        raise Http404("Property not found")

    if request.user.is_authenticated:
        recent = request.session.get('recently_viewed_property_ids', [])
        recent = [pid for pid in recent if pid != property_obj.pk]
        recent.insert(0, property_obj.pk)
        request.session['recently_viewed_property_ids'] = recent[:10]

    gallery = [photo.image.url for photo in property_obj.photos.all()]
    saved_ids = _saved_ids_for(request.user)

    similar_properties = [
        _property_card_context(p, saved_ids) for p in Property.objects.filter(
            status=Property.Status.PUBLISHED, city=property_obj.city,
        ).exclude(pk=pk).prefetch_related('photos', 'amenities')[:2]
    ]

    property_details_table = [
        (label, value) for label, value in [
            ('Property Type', property_obj.get_property_type_display() if property_obj.property_type else ''),
            ('Bedrooms', property_obj.bedrooms),
            ('Bathrooms', property_obj.bathrooms),
            ('Balconies', property_obj.balconies),
            ('Carpet Area', f'{property_obj.carpet_area} sq.ft.' if property_obj.carpet_area else ''),
            ('Built-up Area', f'{property_obj.built_up_area} sq.ft.' if property_obj.built_up_area else ''),
            ('Floor', property_obj.floor_label),
            ('Property Age', property_obj.get_property_age_display() if property_obj.property_age else ''),
            ('Facing', property_obj.get_facing_display() if property_obj.facing else ''),
            ('Furnishing', property_obj.get_furnishing_status_display() if property_obj.furnishing_status else ''),
            ('Tenant Preference', ', '.join(
                dict(Property.TenantPreference.choices).get(p, p) for p in property_obj.tenant_preferences
            )),
        ] if value not in (None, '')
    ]

    amenities = [{'icon': a.icon, 'label': a.name} for a in property_obj.amenities.all()]

    reviews = Review.objects.filter(property=property_obj).select_related('tenant')
    review_average = reviews.aggregate(avg=Avg('rating'))['avg']
    review_count = reviews.count()
    user_review = None
    can_review = False
    if request.user.is_authenticated and request.user.role == 'tenant':
        user_review = reviews.filter(tenant=request.user).first()
        can_review = user_review is not None or Visit.objects.filter(
            tenant=request.user, property=property_obj, status=Visit.Status.COMPLETED,
        ).exists()

    context = {
        "reviews": reviews,
        "review_average": review_average,
        "review_count": review_count,
        "user_review": user_review,
        "can_review": can_review,
        "property": _property_card_context(property_obj, saved_ids) | {'id': property_obj.pk},
        "property_description": property_obj.description,
        "contact_options": _owner_contact_options(property_obj),
        "gallery": gallery,
        "amenities": amenities,
        "property_details_table": property_details_table,
        "similar_properties": similar_properties,
        "owner": {
            "name": property_obj.owner.full_name,
            "initials": (property_obj.owner.full_name or '?')[0].upper(),
            "member_since": property_obj.owner.date_joined.strftime('%B %Y'),
        },
        "rent_details": {
            "deposit": property_obj.security_deposit or 0,
            "maintenance": property_obj.maintenance_charges or 0,
            "available_from": property_obj.available_from.strftime('%d %b %Y') if property_obj.available_from else 'Immediately',
        },
    }
    return render(request, "properties/property_detail.html", context)


@tenant_required
@require_POST
def toggle_saved(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, status=Property.Status.PUBLISHED)
    saved, created = SavedProperty.objects.get_or_create(tenant=request.user, property=property_obj)
    if not created:
        saved.delete()
        messages.success(request, 'Removed from saved properties.')
    else:
        messages.success(request, 'Saved to your dashboard.')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = 'properties:search'
    return redirect(next_url)
