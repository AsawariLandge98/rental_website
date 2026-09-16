from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('become-a-host/', views.become_host, name='become_host'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('legal/<slug:slug>/', views.legal_page, name='legal_page'),
    path('newsletter/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
