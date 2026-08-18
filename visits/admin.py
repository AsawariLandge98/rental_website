from django.contrib import admin

from .models import Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'property', 'scheduled_at', 'status']
    list_filter = ['status']
    search_fields = ['tenant__email', 'property__title']
