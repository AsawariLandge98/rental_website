from django.shortcuts import render

# Placeholder listings until a real RoommateProfile model exists. Cards show
# a photo of the actual flat/room being shared (matching property cards),
# not a stock photo of the person — sourced from the same Unsplash image
# pool already used elsewhere in this codebase.
ROOMMATES = [
    {
        "name": "Arjun Sharma",
        "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=70",
        "badge": "Available Now",
        "badge_color": "green",
        "occupation": "Working Professional",
        "gender": "Male",
        "age": 26,
        "room_type": "2 BHK Apartment",
        "location": "Koramangala, Bengaluru",
        "price": 8000,
    },
    {
        "name": "Priya Singh",
        "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=70",
        "badge": "Available Now",
        "badge_color": "green",
        "occupation": "Working Professional",
        "gender": "Female",
        "age": 24,
        "room_type": "3 BHK Apartment",
        "location": "Koramangala 4th Block",
        "price": 7500,
    },
    {
        "name": "Karan Patel",
        "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=70",
        "badge": "Looking for 1",
        "badge_color": "blue",
        "occupation": "Working Professional",
        "gender": "Male",
        "age": 27,
        "room_type": "3 BHK Apartment",
        "location": "HSR Layout, Bengaluru",
        "price": 9000,
    },
    {
        "name": "Sneha Reddy",
        "image": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=70",
        "badge": "Available Now",
        "badge_color": "green",
        "occupation": "Student",
        "gender": "Female",
        "age": 22,
        "room_type": "Shared Room in 2 BHK",
        "location": "Bellandur, Bengaluru",
        "price": 6000,
    },
    {
        "name": "Rohit Verma",
        "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=800&q=70",
        "badge": "Available This Month",
        "badge_color": "gold",
        "occupation": "Working Professional",
        "gender": "Male",
        "age": 25,
        "room_type": "Private Room in 3 BHK",
        "location": "Koramangala 8th Block",
        "price": 10000,
    },
    {
        "name": "Nikhil & Aditya",
        "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=70",
        "badge": "Looking for 2",
        "badge_color": "blue",
        "occupation": "Students",
        "gender": "Male",
        "age": "21 & 21",
        "room_type": "2 BHK Apartment",
        "location": "BTM Layout, Bengaluru",
        "price": 5500,
    },
    {
        "name": "Megha Iyer",
        "image": "https://images.unsplash.com/photo-1518780664697-55e3ad937233?auto=format&fit=crop&w=800&q=70",
        "badge": "Available Now",
        "badge_color": "green",
        "occupation": "Working Professional",
        "gender": "Female",
        "age": 25,
        "room_type": "Private Room in 2 BHK",
        "location": "Whitefield, Bengaluru",
        "price": 9500,
    },
    {
        "name": "Vikram Joshi",
        "image": "https://images.unsplash.com/photo-1449158743715-0a90ebb6d2d8?auto=format&fit=crop&w=800&q=70",
        "badge": "Available Now",
        "badge_color": "green",
        "occupation": "Working Professional",
        "gender": "Male",
        "age": 28,
        "room_type": "2 BHK Apartment",
        "location": "Marathahalli, Bengaluru",
        "price": 8500,
    },
]

GENDER_OPTIONS = ['Male', 'Female']

BUDGET_OPTIONS = [
    ('0-7000', 'Under ₹7,000'),
    ('7000-9000', '₹7,000 - ₹9,000'),
    ('9000-', 'Above ₹9,000'),
]


def roommate_list(request):
    room_type_options = sorted({r['room_type'] for r in ROOMMATES})

    selected_gender = request.GET.get('gender', '')
    selected_room_type = request.GET.get('room_type', '')
    selected_budget = request.GET.get('budget', '')
    selected_q = request.GET.get('q', '').strip()

    roommates = ROOMMATES
    if selected_gender in GENDER_OPTIONS:
        roommates = [r for r in roommates if r['gender'] == selected_gender]
    if selected_room_type in room_type_options:
        roommates = [r for r in roommates if r['room_type'] == selected_room_type]
    if selected_budget:
        lo_str, _, hi_str = selected_budget.partition('-')
        lo = int(lo_str) if lo_str else 0
        hi = int(hi_str) if hi_str else None
        roommates = [r for r in roommates if r['price'] >= lo and (hi is None or r['price'] <= hi)]
    if selected_q:
        q = selected_q.lower()
        roommates = [r for r in roommates if q in r['location'].lower()]

    context = {
        "roommates": roommates,
        "result_count": len(roommates),
        "gender_options": GENDER_OPTIONS,
        "room_type_options": room_type_options,
        "budget_options": BUDGET_OPTIONS,
        "selected_gender": selected_gender,
        "selected_room_type": selected_room_type,
        "selected_budget": selected_budget,
        "selected_q": selected_q,
    }
    return render(request, "roommates/list.html", context)
