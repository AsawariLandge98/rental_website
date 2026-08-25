from django.shortcuts import render

# Placeholder listings until a real Stay/Hotel model exists. Each stay's
# `property_type` is a real, filterable field (not a marketing label like
# the old "Popular" tag was) — it's also what renders as the card badge.
STAYS = [
    {
        "id": 1,
        "title": "The Himalyan Retreat",
        "location": "Manali, Himachal Pradesh",
        "property_type": "Resort",
        "price": 4200,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "coffee", "label": "Breakfast"},
            {"icon": "commercial", "label": "Parking"},
            {"icon": "mountain", "label": "Mountain View"},
        ],
        "image": "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?auto=format&fit=crop&w=800&q=70",
    },
    {
        "id": 2,
        "title": "Snow Valley Homestay",
        "location": "Manali, Himachal Pradesh",
        "property_type": "Homestay",
        "price": 2800,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "coffee", "label": "Breakfast"},
            {"icon": "house", "label": "Kitchen"},
            {"icon": "commercial", "label": "Free Parking"},
        ],
        "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=70",
    },
    {
        "id": 3,
        "title": "Hotel Pine View",
        "location": "Manali, Himachal Pradesh",
        "property_type": "Hotel",
        "price": 5600,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "utensils", "label": "Restaurant"},
            {"icon": "commercial", "label": "Parking"},
            {"icon": "bell", "label": "Room Service"},
        ],
        "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=70",
    },
    {
        "id": 4,
        "title": "Riverside Cottages",
        "location": "Manali, Himachal Pradesh",
        "property_type": "Homestay",
        "price": 3200,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "coffee", "label": "Breakfast"},
            {"icon": "house", "label": "Kitchen"},
            {"icon": "droplet", "label": "River View"},
        ],
        "image": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=800&q=70",
    },
]

BUDGET_OPTIONS = [
    ('0-3000', 'Under ₹3,000'),
    ('3000-5000', '₹3,000 - ₹5,000'),
    ('5000-', 'Above ₹5,000'),
]


def hotel_list(request):
    property_type_options = sorted({s['property_type'] for s in STAYS})

    selected_property_type = request.GET.get('property_type', '')
    selected_budget = request.GET.get('budget', '')
    selected_q = request.GET.get('q', '').strip()

    stays = STAYS
    if selected_property_type in property_type_options:
        stays = [s for s in stays if s['property_type'] == selected_property_type]
    if selected_budget:
        lo_str, _, hi_str = selected_budget.partition('-')
        lo = int(lo_str) if lo_str else 0
        hi = int(hi_str) if hi_str else None
        stays = [s for s in stays if s['price'] >= lo and (hi is None or s['price'] <= hi)]
    if selected_q:
        q = selected_q.lower()
        stays = [s for s in stays if q in s['location'].lower()]

    context = {
        "stays": stays,
        "result_count": len(stays),
        "property_type_options": property_type_options,
        "budget_options": BUDGET_OPTIONS,
        "selected_property_type": selected_property_type,
        "selected_budget": selected_budget,
        "selected_q": selected_q,
    }
    return render(request, "hotels/list.html", context)
