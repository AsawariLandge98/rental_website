from django.db import migrations

# The Feature 17 seed migration (0007) set support_email to
# 'support@rentora.local' as a stand-in — '.local' isn't a real,
# deliverable domain, and it's rendered live as a clickable mailto: link in
# the site footer. Swaps it for the one real inbox this project already
# sends mail from (Feature 21's SMTP account) so nothing on the live site
# points at an address that bounces. Only touches the row if it still has
# the exact placeholder value — an admin who already edited it via the CMS
# (Settings) is left alone.
OLD_PLACEHOLDER = 'support@rentora.local'
NEW_EMAIL = 'rentora600@gmail.com'


def fix_placeholder_email(apps, schema_editor):
    SiteSettings = apps.get_model('cms', 'SiteSettings')
    SiteSettings.objects.filter(pk=1, support_email=OLD_PLACEHOLDER).update(support_email=NEW_EMAIL)


def revert_email(apps, schema_editor):
    SiteSettings = apps.get_model('cms', 'SiteSettings')
    SiteSettings.objects.filter(pk=1, support_email=NEW_EMAIL).update(support_email=OLD_PLACEHOLDER)


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0011_alter_sitesettings_favicon_alter_sitesettings_logo_and_more'),
    ]

    operations = [
        migrations.RunPython(fix_placeholder_email, revert_email),
    ]
