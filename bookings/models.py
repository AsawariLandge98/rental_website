from django.conf import settings
from django.db import models

from properties.models import Property


class Booking(models.Model):
    """A tenant's request to book a Hotel / Guest House / Homestay listing
    for a date range. The owner must approve it before it's confirmed —
    same "Request to Book" pattern as Visit, not an instant paid booking
    (no payment gateway wired into this yet)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        CONFIRMED = 'confirmed', 'Confirmed'
        DECLINED = 'declined', 'Declined'
        CANCELLED = 'cancelled', 'Cancelled'

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Booking for {self.property} by {self.tenant} ({self.check_in} to {self.check_out})'

    # Plain methods, not @property — the FK field above is itself named
    # `property`, which shadows the `property` builtin for the rest of this
    # class body. Django templates call no-arg methods automatically, so
    # {{ booking.nights }} / {{ booking.total_price }} still work the same.
    def nights(self):
        return (self.check_out - self.check_in).days

    def total_price(self):
        if self.property.nightly_rate is None:
            return None
        return self.property.nightly_rate * self.nights()
