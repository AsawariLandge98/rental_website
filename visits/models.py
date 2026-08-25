from django.conf import settings
from django.db import models

from properties.models import Property


class Visit(models.Model):
    """A tenant-requested property visit. The owner must approve it before
    it's confirmed (see the owner-side Approve/Decline actions) — a
    deliberate reversal of this model's original no-gate design, requested
    directly by the property owner."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        SCHEDULED = 'scheduled', 'Scheduled'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visits')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'Visit for {self.property} by {self.tenant} at {self.scheduled_at}'
