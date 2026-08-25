from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.TENANT)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.SUPER_ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        TENANT = 'tenant', 'Tenant / Renter'
        OWNER = 'owner', 'Property Owner'
        HOTEL = 'hotel', 'Hotel / Homestay Owner'
        ADMIN = 'admin', 'Admin'
        SUPER_ADMIN = 'super_admin', 'Super Admin'

    INTERNAL_ROLES = (Role.ADMIN, Role.SUPER_ADMIN)
    PUBLIC_ROLES = (Role.TENANT, Role.OWNER, Role.HOTEL)

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TENANT)

    is_email_verified = models.BooleanField(default=False)
    is_mobile_verified = models.BooleanField(default=False)
    accepted_terms = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.full_name} <{self.email}>'

    @property
    def is_internal(self):
        return self.role in self.INTERNAL_ROLES


class TenantProfile(models.Model):
    """Tenant-only profile/preference data, kept off the core `User` model
    since owner/hotel/admin accounts don't need any of these fields."""

    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', 'Apartment'
        INDEPENDENT_HOUSE = 'independent_house', 'Independent House'
        VILLA = 'villa', 'Villa'
        ROOM = 'room', 'Room'
        PG = 'pg', 'PG Accommodation'
        SHARED = 'shared', 'Shared Accommodation'

    class Furnishing(models.TextChoices):
        UNFURNISHED = 'unfurnished', 'Unfurnished'
        SEMI_FURNISHED = 'semi_furnished', 'Semi Furnished'
        FULLY_FURNISHED = 'fully_furnished', 'Fully Furnished'

    class TenantType(models.TextChoices):
        FAMILY = 'family', 'Family'
        BACHELOR = 'bachelor', 'Bachelor'
        PROFESSIONALS = 'professionals', 'Working Professionals'
        STUDENTS = 'students', 'Students'

    class MoveInTime(models.TextChoices):
        IMMEDIATE = 'immediate', 'Immediately'
        WITHIN_1_MONTH = 'within_1_month', 'Within 1 Month'
        WITHIN_3_MONTHS = 'within_3_months', 'Within 3 Months'
        FLEXIBLE = 'flexible', 'Flexible'

    class Language(models.TextChoices):
        ENGLISH = 'en', 'English'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tenant_profile')

    # Personal info
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    about = models.CharField(max_length=300, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/%Y/%m/', null=True, blank=True)

    # Rental preferences
    preferred_city = models.CharField(max_length=60, blank=True)
    preferred_budget_min = models.PositiveIntegerField(null=True, blank=True)
    preferred_budget_max = models.PositiveIntegerField(null=True, blank=True)
    preferred_property_type = models.CharField(max_length=20, choices=PropertyType.choices, blank=True)
    furnishing_preference = models.CharField(max_length=20, choices=Furnishing.choices, blank=True)
    tenant_type = models.CharField(max_length=20, choices=TenantType.choices, blank=True)
    move_in_time = models.CharField(max_length=20, choices=MoveInTime.choices, blank=True)

    # Notification preferences — real, persisted preferences. Only Email is
    # actually wired to real delivery today (django EMAIL_BACKEND); SMS/Push
    # have no delivery infra yet, same as Listing Plan being "stored for
    # real but not enforced" until Subscriptions is built.
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    visit_reminders = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    new_property_alerts = models.BooleanField(default=True)
    offers_updates = models.BooleanField(default=False)

    # Privacy preferences
    show_profile_to_owners = models.BooleanField(default=True)
    allow_owner_contact = models.BooleanField(default=True)

    language = models.CharField(max_length=5, choices=Language.choices, default=Language.ENGLISH)

    def __str__(self):
        return f'Tenant profile: {self.user}'

    PROFILE_FIELDS = [
        'gender', 'date_of_birth', 'occupation', 'about', 'profile_photo',
        'preferred_city', 'preferred_budget_min', 'preferred_budget_max',
        'preferred_property_type', 'furnishing_preference', 'tenant_type', 'move_in_time',
    ]

    @property
    def completion_percent(self):
        filled = sum(1 for f in self.PROFILE_FIELDS if getattr(self, f))
        return round(filled / len(self.PROFILE_FIELDS) * 100)
