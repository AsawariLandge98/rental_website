from django.shortcuts import render

from properties.models import Property
from properties.views import _property_card_context, _saved_ids_for, _with_rating

# Real Property listings — a "hotel/homestay" is just a Property whose
# category is one of these three, created through the same owner/hotel
# listing wizard everyone else uses (see Property.Category). No separate
# Stay model, no separate wizard.
HOTEL_CATEGORIES = Property.HOTEL_CATEGORIES

BUDGET_OPTIONS = [
    ('0-3000', 'Under ₹3,000'),
    ('3000-5000', '₹3,000 - ₹5,000'),
    ('5000-', 'Above ₹5,000'),
]


def hotel_list(request):
    selected_property_type = request.GET.get('property_type', '')
    selected_budget = request.GET.get('budget', '')
    selected_q = request.GET.get('q', '').strip()

    queryset = _with_rating(Property.objects.filter(
        status=Property.Status.PUBLISHED, category__in=HOTEL_CATEGORIES,
    ).prefetch_related('photos', 'amenities'))

    category_values = [c.value for c in HOTEL_CATEGORIES]
    if selected_property_type in category_values:
        queryset = queryset.filter(category=selected_property_type)
    if selected_budget:
        # Hotel/Guest House/Homestay listings are priced per night — this
        # was filtering on monthly_rent while the UI label reads "Budget
        # (per night)", silently matching against the wrong field.
        lo_str, _, hi_str = selected_budget.partition('-')
        lo = int(lo_str) if lo_str else 0
        hi = int(hi_str) if hi_str else None
        queryset = queryset.filter(nightly_rate__gte=lo)
        if hi is not None:
            queryset = queryset.filter(nightly_rate__lte=hi)
    if selected_q:
        queryset = queryset.filter(city__icontains=selected_q)

    saved_ids = _saved_ids_for(request.user)
    stays = [_property_card_context(p, saved_ids) for p in queryset]

    context = {
        "stays": stays,
        "result_count": len(stays),
        "property_type_options": [(c.value, c.label) for c in HOTEL_CATEGORIES],
        "budget_options": BUDGET_OPTIONS,
        "selected_property_type": selected_property_type,
        "selected_budget": selected_budget,
        "selected_q": selected_q,
    }
    return render(request, "hotels/list.html", context)
