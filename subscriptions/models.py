from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """Admin-managed plan catalog. Separate from Property.listing_plan
    (the existing per-listing display badge from Feature 02) — this is a
    new per-owner billing concept, not a rename of that field."""

    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text='INR per month')
    listing_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text='Max active listings this plan allows. Leave blank for unlimited.',
    )
    priority_listing = models.BooleanField(default=False)
    features = models.TextField(blank=True, help_text='One feature per line, shown on the plan card.')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'price']

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField()

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.owner} — {self.plan} ({self.status})'

    @property
    def is_current(self):
        return self.status == self.Status.ACTIVE and self.current_period_end > timezone.now()


class Payment(models.Model):
    """One row per Razorpay transaction attempt. razorpay_order_id is set
    at order-creation time; razorpay_payment_id/signature only once paid.
    Never trust a client-submitted amount — always re-derive from `plan`."""

    class Status(models.TextChoices):
        CREATED = 'created', 'Created'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='payments')
    subscription = models.ForeignKey(
        Subscription, null=True, blank=True, on_delete=models.SET_NULL, related_name='payments',
    )
    razorpay_order_id = models.CharField(max_length=64)
    razorpay_payment_id = models.CharField(max_length=64, blank=True)
    razorpay_signature = models.CharField(max_length=128, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, help_text='INR')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.owner} — ₹{self.amount} ({self.status})'
