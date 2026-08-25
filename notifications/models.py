from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Category(models.TextChoices):
        INQUIRY = 'inquiry', 'Inquiry'
        VISIT = 'visit', 'Visit'
        TICKET = 'ticket', 'Support Ticket'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.SYSTEM)
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.message


def notify(user, message, category=Notification.Category.SYSTEM, url=''):
    """Small helper other apps call to record a real notification — e.g.
    confirming a tenant's own inquiry/visit action back to them, or alerting
    an owner that a tenant reached out or requested a visit on their listing."""
    return Notification.objects.create(user=user, message=message, category=category, url=url)
