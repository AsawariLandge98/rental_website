from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.plan_list, name='plan_list'),
    path('<int:plan_id>/order/', views.create_order, name='create_order'),
    path('verify/', views.verify_payment, name='verify_payment'),
]
