from django.conf import settings
from django.db import models

from properties.models import Property


class Review(models.Model):
    """A real tenant review of a property — gated on Feature 22's real
    Visit.Status.COMPLETED signal (see reviews/views.py::submit_review):
    only someone who actually completed a visit can leave one, so this
    can't become the kind of fake trust signal this site has deliberately
    avoided everywhere else (no fake "Verified" badges, no fake
    testimonials — see Documentation/Feature 04, 17, 20)."""

    RATING_CHOICES = [(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)]

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'property'], name='one_review_per_tenant_per_property'),
        ]

    def __str__(self):
        return f'{self.rating}-star review of {self.property} by {self.tenant}'
