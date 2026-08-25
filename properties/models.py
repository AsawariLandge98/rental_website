from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models


class Amenity(models.Model):
    class Group(models.TextChoices):
        BASIC = 'basic', 'Basic'
        HOME = 'home', 'Home'
        SOCIETY = 'society', 'Society'

    name = models.CharField(max_length=60, unique=True)
    icon = models.CharField(max_length=40)
    group = models.CharField(max_length=10, choices=Group.choices)

    class Meta:
        verbose_name_plural = 'amenities'
        ordering = ['group', 'name']

    def __str__(self):
        return self.name


class Property(models.Model):
    class Category(models.TextChoices):
        RESIDENTIAL = 'residential', 'Residential Property'
        ROOM = 'room', 'Room'
        PG = 'pg', 'PG Accommodation'
        SHARED = 'shared', 'Shared Accommodation'
        HOTEL = 'hotel', 'Hotel'
        GUEST_HOUSE = 'guest_house', 'Guest House'
        HOMESTAY = 'homestay', 'Homestay'

    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', 'Flat / Apartment'
        INDEPENDENT_HOUSE = 'independent_house', 'Independent House'
        VILLA = 'villa', 'Villa'
        BUILDER_FLOOR = 'builder_floor', 'Builder Floor'
        PENTHOUSE = 'penthouse', 'Penthouse'
        STUDIO = 'studio', 'Studio'
        ROOM = 'room', 'Room'
        OTHER = 'other', 'Other'

    class FurnishingStatus(models.TextChoices):
        UNFURNISHED = 'unfurnished', 'Unfurnished'
        SEMI_FURNISHED = 'semi_furnished', 'Semi-Furnished'
        FULLY_FURNISHED = 'fully_furnished', 'Fully Furnished'

    class PropertyAge(models.TextChoices):
        UNDER_CONSTRUCTION = 'under_construction', 'Under Construction'
        LT_1 = 'lt_1', 'Less than 1 Year'
        Y1_3 = '1_3', '1 - 3 Years'
        Y3_5 = '3_5', '3 - 5 Years'
        Y5_10 = '5_10', '5 - 10 Years'
        GT_10 = 'gt_10', '10+ Years'

    class Facing(models.TextChoices):
        NORTH = 'north', 'North'
        SOUTH = 'south', 'South'
        EAST = 'east', 'East'
        WEST = 'west', 'West'
        NORTH_EAST = 'north_east', 'North-East'
        NORTH_WEST = 'north_west', 'North-West'
        SOUTH_EAST = 'south_east', 'South-East'
        SOUTH_WEST = 'south_west', 'South-West'

    class Parking(models.TextChoices):
        NONE = 'none', 'No Parking'
        BIKE = 'bike', 'Bike Parking'
        CAR = 'car', 'Car Parking'
        BOTH = 'both', 'Both'

    class TenantPreference(models.TextChoices):
        FAMILY = 'family', 'Family'
        BACHELOR_MALE = 'bachelor_male', 'Bachelor Male'
        BACHELOR_FEMALE = 'bachelor_female', 'Bachelor Female'
        BACHELOR_COUPLE = 'bachelor_couple', 'Bachelor / Couple'
        STUDENTS = 'students', 'Students'
        PROFESSIONALS = 'professionals', 'Working Professionals'
        ANYONE = 'anyone', 'Anyone'

    class Duration(models.TextChoices):
        ONE_MONTH = '1_month', '1 Month'
        THREE_MONTHS = '3_months', '3 Months'
        SIX_MONTHS = '6_months', '6 Months'
        ELEVEN_MONTHS = '11_months', '11 Months'
        ONE_YEAR = '1_year', '1 Year'
        FLEXIBLE = 'flexible', 'Flexible'

    class ContactPreference(models.TextChoices):
        CHAT = 'chat', 'Platform Chat'
        CALL = 'call', 'Phone Call'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        EMAIL = 'email', 'Email'

    class ListingPlan(models.TextChoices):
        FREE = 'free', 'Free Listing'
        SILVER = 'silver', 'Silver Listing'
        GOLD = 'gold', 'Gold Listing'
        PREMIUM = 'premium', 'Premium Listing'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        # PENDING_VERIFICATION / PENDING_REVIEW are reserved for when the
        # Admin Dashboard approval workflow (workflow doc Parts 9/11) exists.
        # Nothing in this feature sets a property to those states yet.
        PENDING_VERIFICATION = 'pending_verification', 'Pending Verification'
        PENDING_REVIEW = 'pending_review', 'Pending Review'
        PUBLISHED = 'published', 'Published'
        PAUSED = 'paused', 'Paused'
        RENTED = 'rented', 'Rented'
        ARCHIVED = 'archived', 'Archived'

    MIN_PHOTOS_TO_PUBLISH = 5
    MAX_PHOTOS = 25

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')

    # Step 1 — category (kept separate from step-3 "property type": category is
    # the broad listing category from the doc's Step 1; property_type is the
    # more specific type asked for in Step 3. The doc also lists a duplicate
    # "Property Category" field in Step 3 — that's the same concept as this
    # one, so it isn't asked twice.)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.RESIDENTIAL)

    # Step 3 — property information
    title = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    property_type = models.CharField(max_length=20, choices=PropertyType.choices, blank=True)
    furnishing_status = models.CharField(max_length=20, choices=FurnishingStatus.choices, blank=True)
    property_age = models.CharField(max_length=20, choices=PropertyAge.choices, blank=True)
    total_area = models.PositiveIntegerField(null=True, blank=True, help_text='sq.ft.')
    carpet_area = models.PositiveIntegerField(null=True, blank=True, help_text='sq.ft.')
    built_up_area = models.PositiveIntegerField(null=True, blank=True, help_text='sq.ft.')
    facing = models.CharField(max_length=12, choices=Facing.choices, blank=True)
    floor_number = models.PositiveIntegerField(null=True, blank=True)
    total_floors = models.PositiveIntegerField(null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    balconies = models.PositiveSmallIntegerField(null=True, blank=True)
    parking = models.CharField(max_length=10, choices=Parking.choices, default=Parking.NONE, blank=True)

    # Step 4 — location. Exact address is intentionally never shown to the
    # public (see Property.short_location / display_location below) — only
    # city/area/landmark are, matching the doc's privacy rule; the full
    # address stays hidden until Inquiries (a later feature) approves contact.
    country = models.CharField(max_length=60, default='India')
    state = models.CharField(max_length=60, blank=True)
    district = models.CharField(max_length=60, blank=True)
    city = models.CharField(max_length=60, blank=True)
    area_locality = models.CharField(max_length=100, blank=True)
    landmark = models.CharField(max_length=150, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    full_address = models.CharField(max_length=255, blank=True)

    # Step 5 — tenant preferences (multiple selections allowed)
    tenant_preferences = ArrayField(
        models.CharField(max_length=20, choices=TenantPreference.choices), default=list, blank=True,
    )

    # Step 6 — rent details
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maintenance_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    electricity_charges = models.CharField(max_length=60, blank=True, help_text='e.g. "As per meter" or a flat amount')
    water_charges = models.CharField(max_length=60, blank=True)
    no_brokerage = models.BooleanField(default=True)

    # Step 7 — availability
    available_from = models.DateField(null=True, blank=True)
    minimum_stay = models.CharField(max_length=15, choices=Duration.choices, blank=True)
    preferred_move_in_date = models.DateField(null=True, blank=True)
    lease_duration = models.CharField(max_length=15, choices=Duration.choices, blank=True)

    # Step 8 — amenities
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='properties')

    # Step 11 — contact preferences (Step 10, owner/ID verification, is
    # intentionally not implemented — see feature doc)
    contact_preferences = ArrayField(
        models.CharField(max_length=10, choices=ContactPreference.choices), default=list, blank=True,
    )

    # Step 13 — listing plan. Stored for real, but every plan behaves the
    # same right now (no payment gateway) beyond the display badge — paid
    # enforcement is future work for the Subscriptions feature (Part 12).
    listing_plan = models.CharField(max_length=10, choices=ListingPlan.choices, default=ListingPlan.FREE)

    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)

    # Admin moderation (Feature 07) — post-publish review, not a pre-publish
    # gate (owners still publish instantly, per the Feature 02 decision).
    # verified_at/verified_by are internal admin bookkeeping only, never
    # surfaced as a public "Verified" badge (see badge property below).
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='verified_properties',
    )
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'properties'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f'Draft property #{self.pk}'

    def _joined_location(self, parts):
        """Joins location parts, dropping blanks and case-insensitive
        repeats (e.g. area_locality and city both entered as "Nagpur")."""
        seen = set()
        deduped = []
        for part in parts:
            if not part or part.lower() in seen:
                continue
            seen.add(part.lower())
            deduped.append(part)
        return ', '.join(deduped)

    @property
    def short_location(self):
        return self._joined_location([self.area_locality, self.city])

    @property
    def display_location(self):
        return self._joined_location([self.area_locality, self.city, self.state, self.pincode])

    @property
    def floor_label(self):
        if self.floor_number is None:
            return ''
        if self.total_floors:
            return f'Floor {self.floor_number} of {self.total_floors}'
        return f'Floor {self.floor_number}'

    @property
    def cover_photo(self):
        return self.photos.filter(is_cover=True).first() or self.photos.first()

    @property
    def badge(self):
        """Display badge derived from the (real, stored) listing plan —
        never from admin verification, which is internal moderation
        bookkeeping (Feature 07), not a claim shown to tenants."""
        return {'premium': 'premium', 'gold': 'featured'}.get(self.listing_plan)

    @property
    def verification_state(self):
        """Admin-moderation state, independent of `status` (owners still
        publish instantly — see Feature 07). One of 'rejected', 'verified',
        'pending'."""
        if self.rejection_reason:
            return 'rejected'
        if self.verified_at:
            return 'verified'
        return 'pending'

    REQUIRED_FOR_PUBLISH = [
        ('title', 'Property Title'),
        ('description', 'Property Description'),
        ('property_type', 'Property Type'),
        ('city', 'City'),
        ('area_locality', 'Area / Locality'),
        ('monthly_rent', 'Monthly Rent'),
    ]

    def missing_publish_requirements(self):
        missing = [label for field, label in self.REQUIRED_FOR_PUBLISH if not getattr(self, field)]
        if self.photos.count() < self.MIN_PHOTOS_TO_PUBLISH:
            missing.append(f'At least {self.MIN_PHOTOS_TO_PUBLISH} photos (currently {self.photos.count()})')
        return missing

    @property
    def can_publish(self):
        return not self.missing_publish_requirements()


class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='properties/%Y/%m/')
    caption = models.CharField(max_length=60, blank=True)
    is_cover = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.caption or f'Photo #{self.pk}'


class SavedProperty(models.Model):
    """A tenant's shortlist entry. Lives here (not in `dashboard`) so
    `_property_card_context` can compute `is_saved` for the heart icon
    without `properties` depending on `dashboard`."""
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-saved_at']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'property'], name='unique_saved_property'),
        ]

    def __str__(self):
        return f'{self.tenant} saved {self.property}'
