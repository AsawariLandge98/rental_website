from django.conf import settings
from django.db import models

from properties.models import Property


class Inquiry(models.Model):
    """A tenant's direct message to a property owner. No approval gate —
    the owner's contact details are already visible on the property page
    without one (see properties/views.py::_owner_contact_options), so this
    just records that the tenant reached out and lets them track it."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        CLOSED = 'closed', 'Closed'

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inquiries')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f'Inquiry from {self.tenant} for {self.property}'
