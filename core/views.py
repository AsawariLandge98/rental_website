from django.shortcuts import render

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

HERO_IMAGES = [
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=70",
    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=70",
]

# Placeholder listings until the `properties` app has real models.
# ids intentionally match properties.views.PROPERTIES so links resolve to a detail page.
FEATURED_PROPERTIES = [
    {
        "id": 1,
        "title": "2 BHK Apartment for Rent in Koramangala",
        "location": "Koramangala, Bengaluru",
        "beds": 2,
        "baths": 2,
        "area": 1200,
        "price": 24000,
        "badge": "verified",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=60",
    },
    {
        "id": 2,
        "title": "3 BHK Apartment",
        "location": "Koramangala, Bengaluru",
        "beds": 3,
        "baths": 3,
        "area": 1500,
        "price": 45000,
        "badge": "featured",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=60",
    },
    {
        "id": 3,
        "title": "4 BHK Independent House",
        "location": "Sushant Lok, Gurugram",
        "beds": 4,
        "baths": 4,
        "area": 2400,
        "price": 75000,
        "badge": "verified",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=800&q=60",
    },
    {
        "id": 4,
        "title": "1 RK Studio Apartment",
        "location": "Andheri West, Mumbai",
        "beds": 1,
        "baths": 1,
        "area": 450,
        "price": 18000,
        "badge": "premium",
        "no_brokerage": True,
        "image": "https://images.unsplash.com/photo-1560185893-a55cbc8c57e8?auto=format&fit=crop&w=800&q=60",
    },
]

WHY_CHOOSE_US = [
    {"icon": "heart", "title": "Zero Brokerage", "text": "No hidden charges. Deal directly with owners."},
    {"icon": "shield-check", "title": "100% Verified", "text": "Properties, owners & documents verified."},
    {"icon": "lock", "title": "Secure & Safe", "text": "Your data and payments are always protected."},
    {"icon": "chat", "title": "Direct Contact", "text": "Connect directly with property owners."},
    {"icon": "map-pin", "title": "Trusted by Thousands", "text": "Join thousands of happy renters across India."},
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
        "quote": "Found my dream home within a week! The verification process gave me complete peace of mind.",
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
    context = {
        "property_types": PROPERTY_TYPES,
        "hero_images": HERO_IMAGES,
        "featured_properties": FEATURED_PROPERTIES,
        "why_choose_us": WHY_CHOOSE_US,
        "how_it_works": HOW_IT_WORKS,
        "testimonials": TESTIMONIALS,
    }
    return render(request, "core/home.html", context)
