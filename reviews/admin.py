from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tenant', 'property', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['tenant__full_name', 'tenant__email', 'property__title', 'comment']
