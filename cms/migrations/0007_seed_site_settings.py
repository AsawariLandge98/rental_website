from django.db import migrations

# Carries forward the phone/email that were hardcoded and duplicated across
# dashboard/help_support.html and dashboard/owner_help_support.html into the
# one real settings row, so nothing changes on the surface but there's now
# a single source of truth an admin can edit. Social links are left blank —
# no real URLs existed anywhere in the codebase to migrate (they were dead
# `#` links in the footer), so we don't fabricate them.


def seed_site_settings(apps, schema_editor):
    SiteSettings = apps.get_model('cms', 'SiteSettings')
    SiteSettings.objects.get_or_create(
        pk=1, defaults={'support_phone': '+91 98765 43210', 'support_email': 'support@rentora.local'},
    )


def unseed_site_settings(apps, schema_editor):
    SiteSettings = apps.get_model('cms', 'SiteSettings')
    SiteSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0006_seed_legal_pages'),
    ]

    operations = [
        migrations.RunPython(seed_site_settings, unseed_site_settings),
    ]
