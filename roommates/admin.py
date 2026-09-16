from django.contrib import admin

from .models import RoommatePosting


@admin.register(RoommatePosting)
class RoommatePostingAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'poster', 'posting_type', 'monthly_rent', 'is_active', 'created_at']
    list_filter = ['posting_type', 'is_active', 'gender_preference', 'occupation']
    search_fields = ['city', 'area_locality', 'room_type', 'poster__full_name', 'poster__email']
