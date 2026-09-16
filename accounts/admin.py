from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import MobileOTP, TenantProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ['-date_joined']
    list_display = ['email', 'full_name', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'full_name', 'mobile_number']
    readonly_fields = ['date_joined', 'last_login']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'mobile_number', 'role')}),
        ('Verification', {'fields': ('is_email_verified', 'is_mobile_verified', 'accepted_terms')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(TenantProfile)
class TenantProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_city', 'occupation']
    search_fields = ['user__email', 'user__full_name']


@admin.register(MobileOTP)
class MobileOTPAdmin(admin.ModelAdmin):
    """Read-only-in-spirit — for debugging the OTP flow, not for issuing
    or editing codes by hand."""
    list_display = ['user', 'mobile_number', 'is_used', 'attempts', 'created_at', 'expires_at']
    list_filter = ['is_used']
    search_fields = ['user__email', 'mobile_number']
    readonly_fields = ['user', 'mobile_number', 'code', 'attempts', 'is_used', 'created_at', 'expires_at']
