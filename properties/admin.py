from django.contrib import admin

from .models import Amenity, Property, PropertyPhoto, SavedProperty


class PropertyPhotoInline(admin.TabularInline):
    model = PropertyPhoto
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'city', 'status', 'monthly_rent', 'created_at']
    list_filter = ['status', 'category', 'listing_plan']
    search_fields = ['title', 'city', 'area_locality', 'owner__email']
    inlines = [PropertyPhotoInline]


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'icon']
    list_filter = ['group']


@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'property', 'saved_at']
    search_fields = ['tenant__email', 'property__title']
