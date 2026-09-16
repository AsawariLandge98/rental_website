from django.db import migrations

# Migrated verbatim from the hardcoded Python lists that used to live in
# core/views.py (WHY_CHOOSE_US, HOW_IT_WORKS, ABOUT_VALUES, ABOUT_WHY_CHOOSE,
# HOW_TRUST_WORKS, BECOME_HOST_STEPS, BECOME_HOST_PERKS) — same pattern as
# 0002_seed_faqs.py migrating the old hardcoded FAQ lists.

HOME_WHY_CHOOSE = [
    ('heart', 'Zero Brokerage', 'No hidden charges. Deal directly with owners.'),
    ('chat', 'Direct Contact', 'Call, WhatsApp or email owners directly — no waiting.'),
    ('lock', 'Secure & Safe', 'Your data is protected with industry-standard security.'),
    ('calendar', 'Easy Scheduling', 'Request a visit in seconds — the owner confirms it directly.'),
    ('map-pin', 'Real Listings', 'Every listing is posted directly by its actual owner.'),
]

HOME_HOW_IT_WORKS = [
    ('search', '1. Search', 'Search properties as per your need'),
    ('heart', '2. Shortlist', 'Save your favorite properties'),
    ('chat', '3. Connect', 'Connect directly with owners'),
    ('calendar', '4. Visit', 'Schedule visit at your convenience'),
    ('document', '5. Finalize', 'Finalize the deal with confidence'),
    ('key', '6. Move In', 'Move into your new home'),
]

ABOUT_VALUES = [
    ('', 'Transparency in every step', ''),
    ('', 'Safety and security for all users', ''),
    ('', 'Respect and trust in every interaction', ''),
    ('', 'Innovation for a better rental experience', ''),
]

ABOUT_WHY_CHOOSE = [
    ('key', 'Zero Brokerage', 'Save your hard-earned money. Connect directly with property owners.'),
    ('chat', 'Direct Contact', 'Talk directly with owners. No middlemen, no extra charges.'),
    ('calendar', 'Easy Scheduling', 'Request a property visit in seconds — the owner confirms it.'),
    ('lock', 'Secure Platform', 'Your personal data is protected with industry-leading security.'),
    ('map-pin', 'Growing Coverage', 'New cities and properties are added directly by owners, every day.'),
    ('headset', 'Responsive Support', 'Reach our support team any time you need help.'),
]

ABOUT_TRUST_STEPS = [
    ('id-card', '1. Create Account', 'Sign up with your name, email and mobile number.'),
    ('house', '2. Real Listings', 'Owners publish their own properties directly — no middlemen.'),
    ('chat', '3. Direct Contact', 'Reach owners by call, WhatsApp or email, instantly.'),
    ('calendar', '4. Request a Visit', "Pick a time that works for you — the owner confirms it."),
    ('flag', '5. Move In', 'Finalize directly with the owner — zero brokerage, ever.'),
]

HOST_STEPS = [
    ('house', '1. Tell us about your property', 'Choose a category, add your location and the real details tenants care about.'),
    ('camera', '2. Make it stand out', 'Add real photos, amenities and your contact preferences.'),
    ('key', '3. Publish and connect', 'Set your rent and availability, go live, and hear from tenants directly.'),
]

HOST_PERKS = [
    ('heart', 'Zero brokerage, zero listing fees', 'List for free. No commission taken from your rent, ever.'),
    ('chat', 'Direct tenant contact', 'Tenants reach you directly by call, WhatsApp or email — no middlemen.'),
    ('sliders', 'You stay in control', 'Set your own rent, availability and how tenants can reach you.'),
    ('headset', 'Real support when you need it', 'Our team is happy to help if you get stuck putting your listing together.'),
]

GROUPS = [
    ('home_why_choose', HOME_WHY_CHOOSE),
    ('home_how_it_works', HOME_HOW_IT_WORKS),
    ('about_values', ABOUT_VALUES),
    ('about_why_choose', ABOUT_WHY_CHOOSE),
    ('about_trust_steps', ABOUT_TRUST_STEPS),
    ('host_steps', HOST_STEPS),
    ('host_perks', HOST_PERKS),
]


def seed_content_blocks(apps, schema_editor):
    ContentBlock = apps.get_model('cms', 'ContentBlock')
    for placement, items in GROUPS:
        for order, (icon, title, text) in enumerate(items):
            ContentBlock.objects.create(placement=placement, icon=icon, title=title, text=text, order=order)


def unseed_content_blocks(apps, schema_editor):
    ContentBlock = apps.get_model('cms', 'ContentBlock')
    placements = [placement for placement, _ in GROUPS]
    ContentBlock.objects.filter(placement__in=placements).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0004_contentblock_legalpage_sitesettings'),
    ]

    operations = [
        migrations.RunPython(seed_content_blocks, unseed_content_blocks),
    ]
