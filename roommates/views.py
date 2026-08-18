from django.shortcuts import render

# Placeholder listings until a real RoommateProfile model exists.
ROOMMATES = [
    {
        "name": "Arjun Sharma",
        "avatar": "https://i.pravatar.cc/240?img=12",
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
        "avatar": "https://i.pravatar.cc/240?img=47",
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
        "avatar": "https://i.pravatar.cc/240?img=14",
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
        "avatar": "https://i.pravatar.cc/240?img=32",
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
        "avatar": "https://i.pravatar.cc/240?img=13",
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
        "avatar": "https://i.pravatar.cc/240?img=15",
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
        "avatar": "https://i.pravatar.cc/240?img=44",
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
        "avatar": "https://i.pravatar.cc/240?img=51",
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

WHY_CHOOSE = [
    {"icon": "lock", "title": "Safe & Secure", "text": "Your personal details are always protected."},
    {"icon": "heart", "title": "No Brokerage", "text": "Connect directly. Save more."},
    {"icon": "target", "title": "Find the Right Match", "text": "Filter by lifestyle, budget & preferences."},
    {"icon": "headset", "title": "Responsive Support", "text": "Reach our support team any time you need help."},
]

SAFETY_TIPS = [
    "Meet in public places first",
    "Verify profile before sharing details",
    "Trust your instincts",
    "Report any suspicious activity",
]


def roommate_list(request):
    context = {
        "roommates": ROOMMATES,
        "result_count": len(ROOMMATES),
        "why_choose": WHY_CHOOSE,
        "safety_tips": SAFETY_TIPS,
    }
    return render(request, "roommates/list.html", context)
