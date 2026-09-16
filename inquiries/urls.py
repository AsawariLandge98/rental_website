from django.urls import path

from . import views

app_name = 'inquiries'

urlpatterns = [
    path('', views.my_inquiries, name='my_inquiries'),
    path('<int:pk>/', views.inquiry_detail, name='inquiry_detail'),
    path('<int:pk>/close/', views.close_inquiry, name='close_inquiry'),
]
