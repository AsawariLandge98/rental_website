from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from core.validators import MaxFileSizeValidator

# Real allowlist — arbitrary files (.exe, .php, .html/.svg that could be
# served back and executed/rendered) were previously accepted with zero
# validation. Covers what a support ticket plausibly needs: a screenshot or
# a short document.
SUPPORT_ATTACHMENT_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'webp', 'doc', 'docx', 'txt']


class SupportTicket(models.Model):
    class Category(models.TextChoices):
        ACCOUNT = 'account', 'Account'
        PROPERTY = 'property', 'Property'
        INQUIRY = 'inquiry', 'Inquiry / Visit'
        PAYMENT = 'payment', 'Payment'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        RESOLVED = 'resolved', 'Resolved'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=150)
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.OTHER)
    description = models.TextField()
    attachment = models.FileField(
        upload_to='support_tickets/%Y/%m/', null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=SUPPORT_ATTACHMENT_EXTENSIONS), MaxFileSizeValidator(5120)],
        help_text='PDF, image or document — up to 5 MB.',
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    page_url = models.CharField(
        max_length=255, blank=True,
        help_text='Page the user was on when they raised this via the floating help widget.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} ({self.user})'


class AuditLog(models.Model):
    """A real, append-only record of admin moderation actions (block/unblock
    a user, approve/reject a property, close an inquiry, etc.) — never
    edited or deleted through the app UI. `target_repr`/`target_id` are
    plain values, not a FK, so the log stays meaningful and intact even if
    the target row is later changed or deleted."""

    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='audit_log_entries',
    )
    message = models.CharField(max_length=255)
    target_type = models.CharField(max_length=30, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_repr = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message


def log_admin_action(admin, message, target_type='', target_id=None, target_repr=''):
    """Small helper other admin views call to record a real audit entry —
    mirrors notifications.notify()'s helper pattern."""
    return AuditLog.objects.create(
        admin=admin, message=message, target_type=target_type, target_id=target_id, target_repr=target_repr,
    )
