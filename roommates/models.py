from django.conf import settings
from django.db import models
from django.utils import timezone

from core.validators import MaxFileSizeValidator


class RoommatePosting(models.Model):
    """A real roommate listing — replaces the old hardcoded ROOMMATES list
    in views.py. Two distinct posting types, matching what the fake UI
    already promised users: someone who already has a place and wants a
    roommate to join them ("Looking"), vs someone who has a real vacancy to
    offer ("Offering"). Doesn't reuse Property — a "Looking" posting isn't
    a property listing at all, just a person and their (unlisted) flat's
    basic stats; see the CMS Feature 17-style research note in the feature
    doc for why a standalone model was the right call here."""

    class PostingType(models.TextChoices):
        LOOKING = 'looking', 'Looking for a Roommate'
        OFFERING = 'offering', 'Offering a Room'

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        ANY = 'any', 'Any'

    class Occupation(models.TextChoices):
        STUDENT = 'student', 'Student'
        WORKING_PROFESSIONAL = 'working_professional', 'Working Professional'
        ANY = 'any', 'Any'

    poster = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roommate_postings')
    posting_type = models.CharField(max_length=10, choices=PostingType.choices, default=PostingType.OFFERING)
    photo = models.ImageField(upload_to='roommates/%Y/%m/', null=True, blank=True, validators=[MaxFileSizeValidator(2048)])

    room_type = models.CharField(max_length=100, help_text='e.g. "2 BHK Apartment", "Private Room in 3 BHK"')
    city = models.CharField(max_length=60)
    area_locality = models.CharField(max_length=100, blank=True)
    monthly_rent = models.PositiveIntegerField(help_text='Monthly rent / your share, in ₹.')

    gender_preference = models.CharField(max_length=10, choices=Gender.choices, default=Gender.ANY)
    occupation = models.CharField(max_length=25, choices=Occupation.choices, default=Occupation.ANY)
    roommates_needed = models.PositiveSmallIntegerField(
        default=1, help_text='How many roommates are needed (mainly relevant for "Looking for a Roommate" posts).',
    )
    move_in_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, max_length=600)

    is_active = models.BooleanField(default=True, help_text='Turn off once you\'ve found a match — hides it from search.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_posting_type_display()} — {self.room_type} in {self.city}'

    @property
    def display_location(self):
        return ', '.join(p for p in [self.area_locality, self.city] if p)

    @property
    def badge_label(self):
        if self.posting_type == self.PostingType.LOOKING:
            return f'Looking for {self.roommates_needed}'
        if self.move_in_date and self.move_in_date > timezone.now().date():
            return f'Available from {self.move_in_date.strftime("%d %b")}'
        return 'Available Now'

    @property
    def badge_color(self):
        return 'blue' if self.posting_type == self.PostingType.LOOKING else 'green'

    @property
    def poster_age(self):
        """Real age from the poster's own account, if they've set a date of
        birth — never fabricated; simply absent from the card/detail page
        when unset, same honesty rule as everywhere else on this site."""
        dob = self.poster.date_of_birth
        if not dob:
            return None
        today = timezone.now().date()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
