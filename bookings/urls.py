from django.urls import path

from . import views

app_name = 'bookings'

urlpatterns = [
    path('request/<int:property_id>/', views.request_booking, name='request_booking'),
    path('my/', views.my_bookings, name='my_bookings'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]
