from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cms.models import FAQ
from properties.models import Property
from properties.views import BUDGET_OPTIONS, CITY_OPTIONS, _property_card_context, _saved_ids_for
from .forms import ContactForm, NewsletterForm

PROPERTY_TYPES = [
    {"label": "All Properties", "icon": "house", "color": "blue"},
    {"label": "Flats", "icon": "apartment", "color": "purple"},
    {"label": "Independent House", "icon": "house", "color": "orange"},
    {"label": "PG / Hostel", "icon": "bed", "color": "teal"},
    {"label": "Villa", "icon": "villa", "color": "pink"},
    {"label": "Commercial", "icon": "commercial", "color": "green"},
    {"label": "Serviced Apartment", "icon": "building", "color": "blue"},
    {"label": "Plots & Land", "icon": "plot", "color": "orange"},
]

# Real, honest claims only — no "Verified" language anywhere on the site
# since there's no verification system built yet (see Feature 02 doc).
WHY_CHOOSE_US = [
    {"icon": "heart", "title": "Zero Brokerage", "text": "No hidden charges. Deal directly with owners."},
    {"icon": "chat", "title": "Direct Contact", "text": "Call, WhatsApp or email owners directly — no waiting."},
    {"icon": "lock", "title": "Secure & Safe", "text": "Your data is protected with industry-standard security."},
    {"icon": "calendar", "title": "Instant Visits", "text": "Schedule a property visit in seconds, no approval wait."},
    {"icon": "map-pin", "title": "Real Listings", "text": "Every listing is posted directly by its actual owner."},
]

HOW_IT_WORKS = [
    {"icon": "search", "title": "1. Search", "text": "Search properties as per your need"},
    {"icon": "heart", "title": "2. Shortlist", "text": "Save your favorite properties"},
    {"icon": "chat", "title": "3. Connect", "text": "Connect directly with owners"},
    {"icon": "calendar", "title": "4. Visit", "text": "Schedule visit at your convenience"},
    {"icon": "document", "title": "5. Finalize", "text": "Finalize the deal with confidence"},
    {"icon": "key", "title": "6. Move In", "text": "Move into your new home"},
]

TESTIMONIALS = [
    {
        "quote": "Found my dream home within a week! Talking to the owner directly made everything move fast.",
        "name": "Priya Sharma",
        "location": "Hyderabad",
        "avatar": "https://i.pravatar.cc/88?img=47",
        "rating": 5,
    },
    {
        "quote": "No brokerage saved me a huge amount. The platform is easy to use and very reliable.",
        "name": "Rohit Verma",
        "location": "Bengaluru",
        "avatar": "https://i.pravatar.cc/88?img=13",
        "rating": 5,
    },
    {
        "quote": "Direct contact with owners makes everything simple and transparent. Highly recommend Rentora!",
        "name": "Anjali Patel",
        "location": "Pune",
        "avatar": "https://i.pravatar.cc/88?img=32",
        "rating": 5,
    },
]


def home(request):
    saved_ids = _saved_ids_for(request.user)
    featured_properties = [
        _property_card_context(p, saved_ids) for p in
        Property.objects.filter(status=Property.Status.PUBLISHED).prefetch_related('photos').order_by('-created_at')[:4]
    ]
    context = {
        "property_types": PROPERTY_TYPES,
        "featured_properties": featured_properties,
        "why_choose_us": WHY_CHOOSE_US,
        "how_it_works": HOW_IT_WORKS,
        "testimonials": TESTIMONIALS,
        "city_options": CITY_OPTIONS,
        "property_type_options": Property.PropertyType.choices,
        "budget_options": BUDGET_OPTIONS,
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


ABOUT_STATS = [
    {"icon": "users", "value": "15,000+", "label": "Happy Users"},
    {"icon": "building", "value": "25,000+", "label": "Properties Listed"},
    {"icon": "heart", "value": "0%", "label": "Brokerage Fees"},
    {"icon": "commercial", "value": "250+", "label": "Cities Covered"},
    {"icon": "star", "value": "4.6/5", "label": "Average Rating"},
]

ABOUT_VALUES = [
    "Transparency in every step",
    "Safety and security for all users",
    "Respect and trust in every interaction",
    "Innovation for a better rental experience",
]

ABOUT_WHY_CHOOSE = [
    {"icon": "key", "title": "Zero Brokerage", "text": "Save your hard-earned money. Connect directly with property owners."},
    {"icon": "chat", "title": "Direct Contact", "text": "Talk directly with owners. No middlemen, no extra charges."},
    {"icon": "calendar", "title": "Instant Scheduling", "text": "Book a property visit instantly, with no approval wait."},
    {"icon": "lock", "title": "Secure Platform", "text": "Your personal data is protected with industry-leading security."},
    {"icon": "map-pin", "title": "Wide Coverage", "text": "Find properties in 250+ cities across India."},
    {"icon": "headset", "title": "Responsive Support", "text": "Reach our support team any time you need help."},
]

# Real, honest steps describing what actually happens today — replaces a
# previous "5-step verification process" section that described mobile/ID/
# property verification which isn't built (see Feature 02 doc).
HOW_TRUST_WORKS = [
    {"icon": "id-card", "title": "1. Create Account", "text": "Sign up with your name, email and mobile number."},
    {"icon": "house", "title": "2. Real Listings", "text": "Owners publish their own properties directly — no middlemen."},
    {"icon": "chat", "title": "3. Direct Contact", "text": "Reach owners by call, WhatsApp or email, instantly."},
    {"icon": "calendar", "title": "4. Instant Visits", "text": "Schedule a visit at a time that works for you."},
    {"icon": "key", "title": "5. Move In", "text": "Finalize directly with the owner — zero brokerage, ever."},
]


def about(request):
    context = {
        "stats": ABOUT_STATS,
        "values": ABOUT_VALUES,
        "why_choose": ABOUT_WHY_CHOOSE,
        "trust_steps": HOW_TRUST_WORKS,
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
    }
    return render(request, "core/contact.html", context)
