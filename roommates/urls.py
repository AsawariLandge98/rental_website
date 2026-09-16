from django.urls import path

from . import views

app_name = 'roommates'

urlpatterns = [
    path('', views.roommate_list, name='list'),
    path('new/', views.roommate_create, name='create'),
    path('<int:pk>/', views.roommate_detail, name='detail'),
    path('<int:pk>/edit/', views.roommate_edit, name='edit'),
    path('<int:pk>/toggle/', views.roommate_toggle_active, name='toggle_active'),
    path('<int:pk>/delete/', views.roommate_delete, name='delete'),
]
