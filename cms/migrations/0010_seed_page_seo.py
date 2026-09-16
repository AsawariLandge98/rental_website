from django.db import migrations

# Real starter meta copy per page, describing what each page actually is —
# same "migrate real content, not lorem ipsum" pattern as 0002_seed_faqs.py.

PAGES = [
    ('home', 'Rentora | Zero Brokerage Rental Platform', 'Search rentals, PGs, roommates and hotels — connect directly with owners, zero brokerage.'),
    ('about', 'About Us | Rentora', 'Learn how Rentora connects tenants and property owners directly, with zero brokerage.'),
    ('contact', 'Contact Us | Rentora', "Get in touch with Rentora's support team, or browse frequently asked questions."),
    ('become_host', 'Become a Host | Rentora', 'List your property on Rentora for free — zero listing fees, zero commission, direct tenant contact.'),
    ('terms', 'Terms & Conditions | Rentora', "Read Rentora's Terms & Conditions."),
    ('privacy', 'Privacy Policy | Rentora', "Read Rentora's Privacy Policy."),
]


def seed_page_seo(apps, schema_editor):
    PageSEO = apps.get_model('cms', 'PageSEO')
    for page, title, description in PAGES:
        PageSEO.objects.get_or_create(page=page, defaults={'meta_title': title, 'meta_description': description})


def unseed_page_seo(apps, schema_editor):
    PageSEO = apps.get_model('cms', 'PageSEO')
    PageSEO.objects.filter(page__in=[p for p, _, _ in PAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0009_pageseo_sitesettings_facebook_pixel_id_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_page_seo, unseed_page_seo),
    ]
