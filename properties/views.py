from django.http import Http404
from django.shortcuts import render

# Placeholder listings until real Property/Amenity/Review models exist.
# id=1 is the fully detailed demo property; the rest exist to populate the
# search results grid and "Similar Properties" panel.
PROPERTIES = {
    1: {
        "id": 1,
        "title": "2 BHK Apartment for Rent in Koramangala",
        "location": "Koramangala 4th Block, Bengaluru, Karnataka 560034",
        "short_location": "Koramangala, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1200,
        "floor_label": "2nd Floor",
        "furnishing": "Fully Furnished",
        "parking": "1 Car Parking",
        "price": 24000,
        "badge": "featured",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=60",
    },
    2: {
        "id": 2,
        "title": "2.5 BHK Apartment",
        "location": "Koramangala 4th Block, Bengaluru",
        "short_location": "Koramangala 4th Block, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1350,
        "price": 25000,
        "badge": "featured",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=60",
    },
    3: {
        "id": 3,
        "title": "2 BHK Independent House",
        "location": "Koramangala 8th Block, Bengaluru",
        "short_location": "Koramangala 8th Block, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1100,
        "price": 20000,
        "badge": "verified",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=800&q=60",
    },
    4: {
        "id": 4,
        "title": "2 BHK Apartment",
        "location": "Koramangala, Bengaluru",
        "short_location": "Koramangala, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1180,
        "price": 28000,
        "badge": "premium",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=800&q=60",
    },
    5: {
        "id": 5,
        "title": "2 BHK Apartment",
        "location": "Koramangala 5th Block, Bengaluru",
        "short_location": "Koramangala 5th Block, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1150,
        "price": 19500,
        "badge": "verified",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?auto=format&fit=crop&w=800&q=60",
    },
    6: {
        "id": 6,
        "title": "2 BHK Apartment",
        "location": "Koramangala 6th Block, Bengaluru",
        "short_location": "Koramangala 6th Block, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1200,
        "price": 24000,
        "badge": "verified",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=60",
    },
    7: {
        "id": 7,
        "title": "2 BHK Builder Floor",
        "location": "Koramangala 7th Block, Bengaluru",
        "short_location": "Koramangala 7th Block, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1050,
        "price": 18000,
        "badge": "featured",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=60",
    },
    8: {
        "id": 8,
        "title": "2 BHK Apartment",
        "location": "Koramangala, Bengaluru",
        "short_location": "Koramangala, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1220,
        "price": 26000,
        "badge": "verified",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=60",
    },
}

AMENITIES = [
    {"icon": "building", "label": "Lift"},
    {"icon": "commercial", "label": "Car Parking"},
    {"icon": "bolt", "label": "Power Backup"},
    {"icon": "shield-check", "label": "24x7 Security"},
    {"icon": "camera", "label": "CCTV"},
    {"icon": "wifi", "label": "Wi-Fi"},
    {"icon": "snowflake", "label": "AC"},
    {"icon": "grid", "label": "Washing Machine"},
    {"icon": "droplet", "label": "Water Supply"},
    {"icon": "flag", "label": "Gas Pipeline"},
    {"icon": "house", "label": "Modular Kitchen"},
    {"icon": "rows", "label": "Fridge"},
    {"icon": "bed", "label": "Sofa"},
    {"icon": "apartment", "label": "Microwave"},
    {"icon": "droplet", "label": "Geyser"},
]

PRIME_LOCATION = [
    "500 m to Koramangala Metro Station",
    "1.2 km to Forum Mall",
    "1.5 km to St. John's Hospital",
    "2.0 km to Sony World Signal",
]

PROPERTY_DETAILS_TABLE = [
    ("Property Type", "Apartment"),
    ("Bedrooms", "2"),
    ("Bathrooms", "2"),
    ("Balcony", "1"),
    ("Carpet Area", "1100 sq.ft."),
    ("Built-up Area", "1200 sq.ft."),
    ("Floor", "2 of 5"),
    ("Property Age", "3 - 5 Years"),
    ("Facing", "North"),
    ("Furnishing", "Fully Furnished"),
    ("Tenant Preference", "Family / Bachelor"),
    ("Pet Allowed", "No"),
]

RATING_BREAKDOWN = [
    {"stars": 5, "count": 24, "pct": 75},
    {"stars": 4, "count": 5, "pct": 16},
    {"stars": 3, "count": 2, "pct": 6},
    {"stars": 2, "count": 1, "pct": 3},
    {"stars": 1, "count": 0, "pct": 0},
]

REVIEWS = [
    {
        "name": "Priya N.",
        "avatar": "https://i.pravatar.cc/64?img=47",
        "verified": True,
        "date": "2 months ago",
        "rating": 5,
        "comment": "Great place to stay! Well maintained apartment and owner is very responsive.",
    },
    {
        "name": "Rohit K.",
        "avatar": "https://i.pravatar.cc/64?img=13",
        "verified": True,
        "date": "4 months ago",
        "rating": 4,
        "comment": "Very good location and facilities. Highly recommended.",
    },
]


def search_results(request):
    context = {
        "demo_logged_in": True,
        "properties": list(PROPERTIES.values()),
        "result_count": "1,248",
    }
    return render(request, "properties/search_results.html", context)


def property_detail(request, pk):
    property_obj = PROPERTIES.get(pk)
    if not property_obj:
        raise Http404("Property not found")

    gallery = [
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=70",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=70",
    ]

    similar_properties = [p for p in PROPERTIES.values() if p["id"] != pk][:2]

    context = {
        "demo_logged_in": True,
        "property": property_obj,
        "gallery": gallery,
        "amenities": AMENITIES,
        "prime_location": PRIME_LOCATION,
        "property_details_table": PROPERTY_DETAILS_TABLE,
        "rating_average": 4.6,
        "rating_count": 32,
        "rating_breakdown": RATING_BREAKDOWN,
        "reviews": REVIEWS,
        "similar_properties": similar_properties,
        "owner": {
            "name": "Amit Sharma",
            "avatar": "https://i.pravatar.cc/96?img=68",
            "member_since": "June 2022",
            "response_time": "Within a few hours",
        },
        "rent_details": {
            "deposit": 48000,
            "maintenance": 2000,
            "available_from": "15 Jun 2024",
        },
    }
    return render(request, "properties/property_detail.html", context)
