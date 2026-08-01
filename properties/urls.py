from django.urls import path

from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.search_results, name='search'),
    path('<int:pk>/', views.property_detail, name='detail'),
]
