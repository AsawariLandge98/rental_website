from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from accounts.models import User
from cms.models import ContentBlock, FAQ, LegalPage, PageSEO
from properties.models import Property
from properties.views import BUDGET_OPTIONS, _property_card_context, _saved_ids_for, _with_rating, get_city_options
from .forms import ContactForm, NewsletterForm

PROPERTY_TYPES = [
    {"label": "All Properties", "icon": "house"},
    {"label": "Flats", "icon": "apartment"},
    {"label": "Independent House", "icon": "house"},
    {"label": "PG / Hostel", "icon": "bed"},
    {"label": "Villa", "icon": "villa"},
    {"label": "Commercial", "icon": "commercial"},
    {"label": "Serviced Apartment", "icon": "building"},
    {"label": "Plots & Land", "icon": "plot"},
]


def _blocks(placement):
    return ContentBlock.objects.filter(placement=placement, is_published=True)


def _page_seo(page):
    return PageSEO.objects.filter(page=page).first()


def home(request):
    saved_ids = _saved_ids_for(request.user)
    featured_properties = [
        _property_card_context(p, saved_ids) for p in _with_rating(
            Property.objects.filter(status=Property.Status.PUBLISHED).prefetch_related('photos', 'amenities'),
        ).order_by('-created_at')[:12]
    ]
    context = {
        "property_types": PROPERTY_TYPES,
        "featured_properties": featured_properties,
        "why_choose_us": _blocks(ContentBlock.Placement.HOME_WHY_CHOOSE),
        "how_it_works": _blocks(ContentBlock.Placement.HOME_HOW_IT_WORKS),
        "city_options": get_city_options(),
        "property_type_options": Property.PropertyType.choices,
        "budget_options": BUDGET_OPTIONS,
        "page_seo": _page_seo(PageSEO.Page.HOME),
    }
    return render(request, "core/home.html", context)


@require_POST
def subscribe_newsletter(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "You're subscribed! Watch your inbox for new listings.")
    else:
        messages.error(request, ' '.join(e for errs in form.errors.values() for e in errs))

    next_url = request.META.get('HTTP_REFERER') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = 'core:home'
    return redirect(next_url)


def become_host(request):
    context = {
        "steps": _blocks(ContentBlock.Placement.HOST_STEPS),
        "perks": _blocks(ContentBlock.Placement.HOST_PERKS),
        "page_seo": _page_seo(PageSEO.Page.BECOME_HOST),
    }
    return render(request, "core/become_host.html", context)


def about(request):
    published = Property.objects.filter(status=Property.Status.PUBLISHED)
    stats = [
        {"icon": "building", "value": published.count(), "label": "Properties Listed"},
        {"icon": "users", "value": User.objects.filter(role__in=User.PUBLIC_ROLES).count(), "label": "Registered Users"},
        {"icon": "commercial", "value": published.exclude(city='').values('city').distinct().count(), "label": "Cities Covered"},
        {"icon": "heart", "value": "0%", "label": "Brokerage Fees"},
    ]
    context = {
        "stats": stats,
        "values": _blocks(ContentBlock.Placement.ABOUT_VALUES),
        "why_choose": _blocks(ContentBlock.Placement.ABOUT_WHY_CHOOSE),
        "trust_steps": _blocks(ContentBlock.Placement.ABOUT_TRUST_STEPS),
        "page_seo": _page_seo(PageSEO.Page.ABOUT),
    }
    return render(request, "core/about.html", context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for reaching out — we'll get back to you soon.")
            return redirect('core:contact')
    else:
        form = ContactForm()

    context = {
        "faqs": FAQ.objects.filter(placement=FAQ.Placement.CONTACT, is_published=True),
        "form": form,
        "page_seo": _page_seo(PageSEO.Page.CONTACT),
    }
    return render(request, "core/contact.html", context)


def legal_page(request, slug):
    try:
        page = LegalPage.objects.get(slug=slug)
    except LegalPage.DoesNotExist:
        raise Http404('Page not found.')
    return render(request, "core/legal_page.html", {"page": page, "page_seo": _page_seo(slug)})


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse('sitemap'))
    return render(request, "robots.txt", {"sitemap_url": sitemap_url}, content_type="text/plain")
