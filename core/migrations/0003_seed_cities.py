from django.db import migrations

# Carries forward the 4 cities that were hardcoded as CITY_OPTIONS in
# properties/views.py into real, admin-manageable rows — same pattern as
# Feature 11's FAQ seed. Nothing changes on the surface (same 4 cities, same
# order), but an admin can now add/remove cities themselves.

CITIES = ['Bengaluru', 'Hyderabad', 'Mumbai', 'Pune']


def seed_cities(apps, schema_editor):
    City = apps.get_model('core', 'City')
    for order, name in enumerate(CITIES):
        City.objects.get_or_create(name=name, defaults={'order': order})


def unseed_cities(apps, schema_editor):
    City = apps.get_model('core', 'City')
    City.objects.filter(name__in=CITIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_city'),
    ]

    operations = [
        migrations.RunPython(seed_cities, unseed_cities),
    ]
