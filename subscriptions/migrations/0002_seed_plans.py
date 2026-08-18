from django.db import migrations

PLANS = [
    dict(name='Free', price=0, listing_limit=3, priority_listing=False, features='Basic support', order=0),
    dict(name='Silver', price=499, listing_limit=10, priority_listing=False, features='Email & chat support', order=1),
    dict(name='Gold', price=999, listing_limit=25, priority_listing=True, features='Phone, chat & email support', order=2),
    dict(name='Premium', price=1999, listing_limit=None, priority_listing=True, features='Dedicated account manager', order=3),
]


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    for plan in PLANS:
        SubscriptionPlan.objects.create(**plan)


def unseed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('subscriptions', 'SubscriptionPlan')
    SubscriptionPlan.objects.filter(name__in=[p['name'] for p in PLANS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_plans, unseed_plans),
    ]
