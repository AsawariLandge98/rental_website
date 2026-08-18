from django.contrib import admin

from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'placement', 'order', 'is_published', 'updated_at']
    list_filter = ['placement', 'is_published']
    search_fields = ['question', 'answer']
