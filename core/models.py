from django.db import models


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class City(models.Model):
    """The curated list of cities offered in the Search Results / Home
    quick-search city dropdown (properties/views.py::get_city_options()).
    Deliberately NOT a FK target for Property/RoommatePosting/Hotel's own
    `city` text fields — those stay free text so an owner can list in a
    city that isn't in this curated list yet; this model only controls
    what's offered as a quick-pick shortcut. An admin adds a new city here
    themselves, no developer/deploy needed."""

    name = models.CharField(max_length=60, unique=True)
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first in the dropdown.')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'Cities'

    def __str__(self):
        return self.name


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}>'
