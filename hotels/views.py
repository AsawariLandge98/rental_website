from django.shortcuts import render

# Placeholder listings until a real Stay/Hotel model exists.
STAYS = [
    {
        "id": 1,
        "title": "The Himalyan Retreat",
        "location": "Manali, Himachal Pradesh",
        "distance": "2.1 km from Mall Road",
        "tag": "Popular",
        "tag_color": "gold",
        "rating": 4.9,
        "rating_label": "Excellent",
        "reviews": 236,
        "price": 4200,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "coffee", "label": "Breakfast"},
            {"icon": "commercial", "label": "Parking"},
            {"icon": "mountain", "label": "Mountain View"},
        ],
        "image": "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?auto=format&fit=crop&w=800&q=60",
    },
    {
        "id": 2,
        "title": "Snow Valley Homestay",
        "location": "Manali, Himachal Pradesh",
        "distance": "1.3 km from Mall Road",
        "tag": "Homestay",
        "tag_color": "green",
        "rating": 4.6,
        "rating_label": "Excellent",
        "reviews": 189,
        "price": 2800,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "coffee", "label": "Breakfast"},
            {"icon": "house", "label": "Kitchen"},
            {"icon": "commercial", "label": "Free Parking"},
        ],
        "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=60",
    },
    {
        "id": 3,
        "title": "Hotel Pine View",
        "location": "Manali, Himachal Pradesh",
        "distance": "3.4 km from Mall Road",
        "tag": "Hotel",
        "tag_color": "blue",
        "rating": 4.4,
        "rating_label": "Very Good",
        "reviews": 312,
        "price": 5600,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "utensils", "label": "Restaurant"},
            {"icon": "commercial", "label": "Parking"},
            {"icon": "bell", "label": "Room Service"},
        ],
        "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=60",
    },
    {
        "id": 4,
        "title": "Riverside Cottages",
        "location": "Manali, Himachal Pradesh",
        "distance": "5.2 km from Mall Road",
        "tag": "Homestay",
        "tag_color": "green",
        "rating": 4.8,
        "rating_label": "Excellent",
        "reviews": 156,
        "price": 3200,
        "amenities": [
            {"icon": "wifi", "label": "Free Wi-Fi"},
            {"icon": "coffee", "label": "Breakfast"},
            {"icon": "house", "label": "Kitchen"},
            {"icon": "droplet", "label": "River View"},
        ],
        "image": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=800&q=60",
    },
]

WHY_BOOK = [
    {"icon": "heart", "title": "Zero Brokerage", "text": "No hidden charges — book directly with the host."},
    {"icon": "chat", "title": "Direct Contact", "text": "Reach hosts directly, no middlemen involved."},
    {"icon": "lock", "title": "Secure Platform", "text": "Your payment and details are always protected."},
    {"icon": "headset", "title": "Responsive Support", "text": "We're here to help whenever you need it."},
]

SAFETY_TIPS = [
    "Confirm details directly with the host before booking",
    "Avoid sharing personal details outside the platform",
    "Report any suspicious listings",
]


def hotel_list(request):
    context = {
        "stays": STAYS,
        "result_count": len(STAYS),
        "why_book": WHY_BOOK,
        "safety_tips": SAFETY_TIPS,
    }
    return render(request, "hotels/list.html", context)
