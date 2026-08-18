from django.contrib import admin

from .models import Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'property', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['tenant__email', 'property__title']
