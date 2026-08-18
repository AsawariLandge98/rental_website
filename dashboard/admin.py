from django.contrib import admin

from .models import AuditLog, SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'category', 'status', 'created_at']
    list_filter = ['category', 'status']
    search_fields = ['subject', 'user__email', 'description']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['message', 'admin', 'target_type', 'created_at']
    list_filter = ['target_type']
    search_fields = ['message', 'admin__email', 'target_repr']
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
