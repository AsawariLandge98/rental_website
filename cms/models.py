from django.db import models

from core.validators import MaxFileSizeValidator


class SiteSettings(models.Model):
    """Single-row site-wide settings — support contact info and social
    links. Was hardcoded and duplicated across multiple templates before
    (Help & Support pages each had their own copy of the phone/email;
    social links were dead `#` placeholders); this is the one real source
    now, exposed everywhere via cms.context_processors.site_settings."""

    support_phone = models.CharField(max_length=20, blank=True)
    support_email = models.EmailField(blank=True)
    business_address = models.CharField(max_length=255, blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # General / branding — real, wired into header.html/footer.html/the
    # favicon <link> tag. Falls back to the existing hardcoded Rentora mark
    # when unset, same "real when set, honest default otherwise" pattern as
    # the social links above.
    platform_name = models.CharField(max_length=60, default='Rentora')
    logo = models.ImageField(upload_to='branding/', null=True, blank=True, validators=[MaxFileSizeValidator(2048)])
    favicon = models.ImageField(upload_to='branding/', null=True, blank=True, validators=[MaxFileSizeValidator(512)])

    # SEO — real, rendered as actual <meta>/tracking tags in base.html/
    # auth_base.html when set (never fabricated, never shown if blank).
    google_analytics_id = models.CharField(
        max_length=20, blank=True, help_text='e.g. G-XXXXXXXXXX. Leave blank to disable Analytics.',
    )
    facebook_pixel_id = models.CharField(max_length=20, blank=True, help_text='Leave blank to disable the Pixel.')
    og_image = models.ImageField(
        upload_to='branding/', null=True, blank=True, validators=[MaxFileSizeValidator(2048)],
        help_text='Default social-share preview image for pages that don\'t set their own.',
    )

    # Real, previously-hardcoded Property constants (properties/models.py's
    # MIN_PHOTOS_TO_PUBLISH/MAX_PHOTOS) — moved here so Super Admin can
    # actually change them instead of editing code. Not "System Settings"
    # fields cloned from a generic template; these two are genuinely
    # enforced in properties/manage_views.py and properties/models.py.
    max_photos_per_listing = models.PositiveSmallIntegerField(
        default=25, help_text='Maximum photos an owner can upload per listing.',
    )
    min_photos_to_publish = models.PositiveSmallIntegerField(
        default=5, help_text='Minimum photos required before a listing can be published.',
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class PageSEO(models.Model):
    """Real per-page meta title/description for the site's public pages —
    rendered as the actual <title>/<meta name="description"> tags on each
    page when set, falling back to that page's existing hardcoded default
    otherwise. One row per real page (fixed choices, mirrors LegalPage's
    fixed-slug pattern — no add/delete, only edit)."""

    class Page(models.TextChoices):
        HOME = 'home', 'Home'
        ABOUT = 'about', 'About Us'
        CONTACT = 'contact', 'Contact Us'
        BECOME_HOST = 'become_host', 'Become a Host'
        TERMS = 'terms', 'Terms & Conditions'
        PRIVACY = 'privacy', 'Privacy Policy'

    page = models.CharField(max_length=20, choices=Page.choices, unique=True)
    meta_title = models.CharField(max_length=70, blank=True, help_text='Shown in the browser tab and search results.')
    meta_description = models.CharField(max_length=160, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Page SEO'
        verbose_name_plural = 'Page SEO'
        ordering = ['page']

    def __str__(self):
        return self.get_page_display()


class LegalPage(models.Model):
    """Terms & Conditions / Privacy Policy — real pages an admin can edit,
    replacing what were dead `href="#"` links even though registration
    already legally requires accepting them (see accounts.forms)."""

    class Slug(models.TextChoices):
        TERMS = 'terms', 'Terms & Conditions'
        PRIVACY = 'privacy', 'Privacy Policy'

    slug = models.CharField(max_length=20, choices=Slug.choices, unique=True)
    title = models.CharField(max_length=150)
    body = models.TextField(help_text='Plain text — blank lines start a new paragraph.')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['slug']

    def __str__(self):
        return self.title


class ContentBlock(models.Model):
    """An ordered icon+title+text item for one of the public marketing
    sections that used to be hardcoded Python lists in core/views.py (Why
    Choose Us, How It Works, About's values/why-choose/trust-steps, Become
    a Host's steps/perks) — same shape, now admin-editable without a
    deploy. Mirrors FAQ's placement/order/is_published pattern."""

    class Placement(models.TextChoices):
        HOME_WHY_CHOOSE = 'home_why_choose', 'Home — Why Choose Us'
        HOME_HOW_IT_WORKS = 'home_how_it_works', 'Home — How It Works'
        ABOUT_VALUES = 'about_values', 'About — Our Values'
        ABOUT_WHY_CHOOSE = 'about_why_choose', 'About — Why Choose Us'
        ABOUT_TRUST_STEPS = 'about_trust_steps', 'About — How Trust Works'
        HOST_STEPS = 'host_steps', 'Become a Host — Steps'
        HOST_PERKS = 'host_perks', 'Become a Host — Perks'

    placement = models.CharField(max_length=30, choices=Placement.choices)
    icon = models.CharField(
        max_length=30, blank=True,
        help_text='Icon name from the shared icon set, e.g. "shield-check". Leave blank for none.',
    )
    title = models.CharField(max_length=150)
    text = models.CharField(max_length=300, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['placement', 'order', 'id']

    def __str__(self):
        return f'{self.title} ({self.get_placement_display()})'


class FAQ(models.Model):
    class Placement(models.TextChoices):
        CONTACT = 'contact', 'Contact Page'
        TENANT_HELP = 'tenant_help', 'Tenant Help & Support'

    question = models.CharField(max_length=200)
    answer = models.TextField()
    placement = models.CharField(max_length=20, choices=Placement.choices, default=Placement.CONTACT)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['placement', 'order', 'id']

    def __str__(self):
        return self.question
