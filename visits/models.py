from django.conf import settings
from django.db import models

from properties.models import Property


class Visit(models.Model):
    """A tenant-scheduled property visit. No owner-approval gate — the
    visit is confirmed the moment the tenant books it (see
    feedback-low-friction-contact); the owner sees it land in their own
    dashboard once that's built."""

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visits')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'Visit for {self.property} by {self.tenant} at {self.scheduled_at}'
