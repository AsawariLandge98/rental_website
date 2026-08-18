from django.db import migrations

AMENITIES = [
    ('basic', 'Lift', 'building'),
    ('basic', 'Parking', 'commercial'),
    ('basic', 'Water Supply', 'droplet'),
    ('basic', 'Power Backup', 'bolt'),
    ('basic', 'CCTV', 'camera'),
    ('basic', 'Security Guard', 'shield-check'),
    ('home', 'AC', 'snowflake'),
    ('home', 'Refrigerator', 'rows'),
    ('home', 'Washing Machine', 'grid'),
    ('home', 'Bed', 'bed'),
    ('home', 'Sofa', 'sofa'),
    ('home', 'Dining Table', 'table'),
    ('home', 'TV', 'tv'),
    ('home', 'Wi-Fi', 'wifi'),
    ('society', 'Gym', 'dumbbell'),
    ('society', 'Swimming Pool', 'pool'),
    ('society', 'Garden', 'garden'),
    ('society', 'Clubhouse', 'house'),
    ('society', "Children's Play Area", 'playground'),
    ('society', 'Visitor Parking', 'commercial'),
]


def seed_amenities(apps, schema_editor):
    Amenity = apps.get_model('properties', 'Amenity')
    for group, name, icon in AMENITIES:
        Amenity.objects.get_or_create(name=name, defaults={'group': group, 'icon': icon})


def remove_amenities(apps, schema_editor):
    Amenity = apps.get_model('properties', 'Amenity')
    Amenity.objects.filter(name__in=[name for _, name, _ in AMENITIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_amenities, remove_amenities),
    ]
