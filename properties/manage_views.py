from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.decorators import owner_or_hotel_required
from subscriptions.models import Subscription, SubscriptionPlan
from .forms import (
    AmenitiesForm, AvailabilityForm, CategoryForm, ContactPreferenceForm,
    ListingPlanForm, LocationForm, PropertyInfoForm, PropertyPhotoForm, RentDetailsForm,
    TenantPreferenceForm,
)
from .models import Amenity, Property, PropertyPhoto

# Each wizard step after "select category" (handled separately by
# start_listing) maps to the ModelForm that edits it and the template kind
# used to render it. Order here drives Back/Next navigation and the step
# indicator shown on every step page.
STEPS = [
    ('property-info', 'Property Information', PropertyInfoForm, 'generic'),
    ('location', 'Location', LocationForm, 'generic'),
    ('preferences', 'Tenant Preferences', TenantPreferenceForm, 'choices'),
    ('rent', 'Rent Details', RentDetailsForm, 'generic'),
    ('availability', 'Availability', AvailabilityForm, 'generic'),
    ('amenities', 'Amenities', AmenitiesForm, 'amenities'),
    ('photos', 'Photos & Media', None, 'photos'),
    ('contact', 'Contact Preferences', ContactPreferenceForm, 'contact'),
]
STEP_SLUGS = [slug for slug, *_ in STEPS]

# Purely for rendering the step-indicator strip shown on every wizard page.
WIZARD_NAV = [
    (1, 'Category'), (2, 'Property Info'), (3, 'Location'), (4, 'Preferences'),
    (5, 'Rent'), (6, 'Availability'), (7, 'Amenities'), (8, 'Photos'),
    (9, 'Contact'), (10, 'Preview'),
]


def _step_index(slug):
    return STEP_SLUGS.index(slug)


def _next_step_url(property_obj, current_slug):
    idx = _step_index(current_slug)
    if idx + 1 < len(STEP_SLUGS):
        return reverse('properties:manage_step', args=[property_obj.pk, STEP_SLUGS[idx + 1]])
    return reverse('properties:manage_preview', args=[property_obj.pk])


def _prev_step_url(property_obj, current_slug):
    idx = _step_index(current_slug)
    if idx == 0:
        return reverse('properties:my_listings')
    return reverse('properties:manage_step', args=[property_obj.pk, STEP_SLUGS[idx - 1]])


@owner_or_hotel_required
def my_listings(request):
    all_properties = request.user.properties.all()
    stats = {
        'total': all_properties.count(),
        'active': all_properties.filter(status=Property.Status.PUBLISHED).count(),
        'draft': all_properties.filter(status=Property.Status.DRAFT).count(),
        'paused': all_properties.filter(status=Property.Status.PAUSED).count(),
        'archived': all_properties.filter(status__in=[Property.Status.ARCHIVED, Property.Status.RENTED]).count(),
    }

    queryset = all_properties.prefetch_related('photos').annotate(
        inquiries_count=Count('inquiries', distinct=True),
    ).order_by('-created_at')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    property_type = request.GET.get('property_type', '')

    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) | Q(city__icontains=q) | Q(area_locality__icontains=q)
        )
    if status:
        queryset = queryset.filter(status=status)
    if property_type:
        queryset = queryset.filter(property_type=property_type)

    paginator = Paginator(queryset, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    carry_params = request.GET.copy()
    carry_params.pop('page', None)

    context = {
        'properties': page_obj,
        'page_obj': page_obj,
        'carry_qs': carry_params.urlencode(),
        'stats': stats,
        'status_options': Property.Status.choices,
        'property_type_options': Property.PropertyType.choices,
        'selected_q': q,
        'selected_status': status,
        'selected_property_type': property_type,
    }
    return render(request, 'properties/manage/my_listings.html', context)


def _owner_listing_limit(user):
    """None means unlimited. An owner with no active subscription gets
    whichever plan sorts first (the seeded 'Free' plan, order=0) rather
    than a hardcoded number — one source of truth for the cap."""
    subscription = Subscription.objects.filter(
        owner=user, status=Subscription.Status.ACTIVE, current_period_end__gt=timezone.now(),
    ).select_related('plan').first()
    if subscription:
        return subscription.plan.listing_limit
    default_plan = SubscriptionPlan.objects.filter(is_active=True).order_by('order').first()
    return default_plan.listing_limit if default_plan else None


@owner_or_hotel_required
def start_listing(request):
    limit = _owner_listing_limit(request.user)
    if limit is not None and request.user.properties.exclude(status=Property.Status.ARCHIVED).count() >= limit:
        messages.error(
            request,
            f"You've reached your plan's limit of {limit} listings. Upgrade your subscription plan to add more.",
        )
        return redirect('subscriptions:plan_list')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            return redirect('properties:manage_step', pk=property_obj.pk, step=STEP_SLUGS[0])
    else:
        form = CategoryForm()

    return render(request, 'properties/manage/step_category.html', {
        'form': form, 'step_title': 'Select Listing Category', 'step_number': 1, 'wizard_nav': WIZARD_NAV,
    })


@owner_or_hotel_required
def edit_step(request, pk, step):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if step not in STEP_SLUGS:
        return redirect('properties:manage_step', pk=pk, step=STEP_SLUGS[0])

    idx = _step_index(step)
    slug, title, form_class, kind = STEPS[idx]

    if kind == 'photos':
        return _photos_step(request, property_obj, idx)

    if request.method == 'POST':
        form = form_class(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            return redirect(_next_step_url(property_obj, slug))
    else:
        form = form_class(instance=property_obj)

    context = {
        'property': property_obj,
        'form': form,
        'step_slug': slug,
        'step_title': title,
        'step_number': idx + 2,  # +1 for 1-indexed, +1 because category is step 1
        'steps': STEPS,
        'current_index': idx,
        'prev_url': _prev_step_url(property_obj, slug),
        'kind': kind,
        'wizard_nav': WIZARD_NAV,
    }

    if kind == 'amenities':
        context['grouped_amenities'] = [
            (group_value, group_label, Amenity.objects.filter(group=group_value))
            for group_value, group_label in Amenity.Group.choices
        ]
        context['selected_amenity_ids'] = set(property_obj.amenities.values_list('id', flat=True))
        return render(request, 'properties/manage/step_amenities.html', context)

    if kind == 'choices':
        context['choices'] = Property.TenantPreference.choices
        context['selected'] = property_obj.tenant_preferences
        context['field_name'] = 'tenant_preferences'
        return render(request, 'properties/manage/step_choices.html', context)

    if kind == 'contact':
        context['choices'] = Property.ContactPreference.choices
        context['selected'] = property_obj.contact_preferences
        context['field_name'] = 'contact_preferences'
        return render(request, 'properties/manage/step_choices.html', context)

    return render(request, 'properties/manage/step_generic.html', context)


def _photos_step(request, property_obj, idx):
    from cms.models import SiteSettings
    site_settings = SiteSettings.load()
    max_photos = site_settings.max_photos_per_listing

    if request.method == 'POST':
        files = request.FILES.getlist('images')
        remaining = max_photos - property_obj.photos.count()
        if not files:
            messages.error(request, 'Choose at least one photo to upload.')
        elif len(files) > remaining:
            messages.error(request, f'You can add {remaining} more photo(s) — {max_photos} maximum per listing.')
        else:
            has_cover = property_obj.photos.filter(is_cover=True).exists()
            next_order = property_obj.photos.count()
            for i, f in enumerate(files):
                PropertyPhoto.objects.create(
                    property=property_obj, image=f, is_cover=(not has_cover and i == 0),
                    order=next_order + i,
                )
            messages.success(request, f'{len(files)} photo(s) uploaded.')
        return redirect('properties:manage_step', pk=property_obj.pk, step='photos')

    context = {
        'property': property_obj,
        'step_slug': 'photos',
        'step_title': 'Photos & Media',
        'step_number': idx + 2,
        'steps': STEPS,
        'current_index': idx,
        'prev_url': _prev_step_url(property_obj, 'photos'),
        'photos': property_obj.photos.all(),
        'remaining_slots': max_photos - property_obj.photos.count(),
        'max_photos': max_photos,
        'min_photos_to_publish': site_settings.min_photos_to_publish,
        'wizard_nav': WIZARD_NAV,
    }
    return render(request, 'properties/manage/step_photos.html', context)


@owner_or_hotel_required
@require_POST
def delete_photo(request, pk, photo_id):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    photo = get_object_or_404(PropertyPhoto, pk=photo_id, property=property_obj)
    was_cover = photo.is_cover
    photo.image.delete(save=False)
    photo.delete()
    if was_cover:
        new_cover = property_obj.photos.first()
        if new_cover:
            new_cover.is_cover = True
            new_cover.save(update_fields=['is_cover'])
    return redirect('properties:manage_step', pk=pk, step='photos')


@owner_or_hotel_required
@require_POST
def set_cover_photo(request, pk, photo_id):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    get_object_or_404(PropertyPhoto, pk=photo_id, property=property_obj)
    property_obj.photos.update(is_cover=False)
    PropertyPhoto.objects.filter(pk=photo_id, property=property_obj).update(is_cover=True)
    return redirect('properties:manage_step', pk=pk, step='photos')


@owner_or_hotel_required
def preview_listing(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == 'POST':
        plan_form = ListingPlanForm(request.POST, instance=property_obj)
        if plan_form.is_valid():
            plan_form.save()
            messages.success(request, 'Listing plan updated.')
            return redirect('properties:manage_preview', pk=pk)
    else:
        plan_form = ListingPlanForm(instance=property_obj)

    return render(request, 'properties/manage/preview.html', {
        'property': property_obj,
        'plan_form': plan_form,
        'missing': property_obj.missing_publish_requirements(),
        'steps': STEPS,
        'step_number': 10,
        'wizard_nav': WIZARD_NAV,
    })


@owner_or_hotel_required
@require_POST
def publish_listing(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    missing = property_obj.missing_publish_requirements()
    if missing:
        messages.error(request, 'This listing is missing: ' + ', '.join(missing))
        return redirect('properties:manage_preview', pk=pk)

    property_obj.status = Property.Status.PUBLISHED
    if not property_obj.published_at:
        property_obj.published_at = timezone.now()
    property_obj.rejection_reason = ''
    property_obj.save(update_fields=['status', 'published_at', 'rejection_reason'])
    messages.success(request, 'Your listing is live!')
    return redirect('properties:my_listings')


@owner_or_hotel_required
@require_POST
def set_listing_status(request, pk, status):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    allowed = {Property.Status.PUBLISHED, Property.Status.PAUSED, Property.Status.ARCHIVED}
    if status not in allowed:
        raise PermissionDenied('Invalid status change.')
    if status == Property.Status.PUBLISHED and property_obj.missing_publish_requirements():
        messages.error(request, "This listing isn't complete enough to publish yet.")
        return redirect('properties:manage_preview', pk=pk)
    property_obj.status = status
    update_fields = ['status']
    if status == Property.Status.PUBLISHED:
        if not property_obj.published_at:
            property_obj.published_at = timezone.now()
            update_fields.append('published_at')
        property_obj.rejection_reason = ''
        update_fields.append('rejection_reason')
    property_obj.save(update_fields=update_fields)
    messages.success(request, f'Listing marked as {property_obj.get_status_display()}.')
    return redirect('properties:my_listings')


@owner_or_hotel_required
@require_POST
def delete_listing(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    for photo in property_obj.photos.all():
        photo.image.delete(save=False)
    property_obj.delete()
    messages.success(request, 'Listing deleted.')
    return redirect('properties:my_listings')
