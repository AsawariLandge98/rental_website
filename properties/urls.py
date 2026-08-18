from django.urls import path

from inquiries.views import send_inquiry
from visits.views import schedule_visit
from . import manage_views, views

app_name = 'properties'

urlpatterns = [
    path('', views.search_results, name='search'),
    path('<int:pk>/', views.property_detail, name='detail'),
    path('<int:pk>/save/', views.toggle_saved, name='toggle_saved'),
    path('<int:property_id>/inquire/', send_inquiry, name='send_inquiry'),
    path('<int:property_id>/schedule-visit/', schedule_visit, name='schedule_visit'),

    # Owner-facing listing management (login + owner/hotel role required)
    path('manage/', manage_views.my_listings, name='my_listings'),
    path('manage/new/', manage_views.start_listing, name='start_listing'),
    path('manage/<int:pk>/edit/<str:step>/', manage_views.edit_step, name='manage_step'),
    path('manage/<int:pk>/photos/<int:photo_id>/delete/', manage_views.delete_photo, name='delete_photo'),
    path('manage/<int:pk>/photos/<int:photo_id>/cover/', manage_views.set_cover_photo, name='set_cover_photo'),
    path('manage/<int:pk>/preview/', manage_views.preview_listing, name='manage_preview'),
    path('manage/<int:pk>/publish/', manage_views.publish_listing, name='manage_publish'),
    path('manage/<int:pk>/status/<str:status>/', manage_views.set_listing_status, name='manage_set_status'),
    path('manage/<int:pk>/delete/', manage_views.delete_listing, name='manage_delete'),
]
