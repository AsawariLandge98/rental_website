from django.urls import path

from . import views

app_name = 'roommates'

urlpatterns = [
    path('', views.roommate_list, name='list'),
]
