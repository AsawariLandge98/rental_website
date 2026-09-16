from django.contrib import admin

from .models import ContentBlock, FAQ, LegalPage, SiteSettings


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'placement', 'order', 'is_published', 'updated_at']
    list_filter = ['placement', 'is_published']
    search_fields = ['question', 'answer']


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'placement', 'order', 'is_published', 'updated_at']
    list_filter = ['placement', 'is_published']
    search_fields = ['title', 'text']


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'updated_at']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['support_phone', 'support_email', 'updated_at']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
