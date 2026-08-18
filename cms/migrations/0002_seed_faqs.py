from django.db import migrations

CONTACT_FAQS = [
    ("How do I list my property on Rentora?", "Create a free account, click \"List Your Property\" and fill in the details — your listing goes live as soon as you publish it."),
    ("How do I contact a property owner?", "Open any property's detail page and use the Contact Owner button to message or call them directly."),
    ("Is there any brokerage or hidden charge?", "No. Rentora is a zero-brokerage platform — you deal with owners directly, with no hidden fees."),
    ("Can I schedule a visit before finalizing?", "Yes — request a visit slot directly from the property detail page and it's confirmed instantly."),
    ("Is my personal information safe with Rentora?", "Yes, your data is encrypted and never shared with third parties without your consent."),
]

TENANT_HELP_FAQS = [
    ('How can I contact a property owner?', 'Open any published listing and use the Call, WhatsApp or Email buttons — owner contact details are shown directly on every property page, no approval wait required.'),
    ('How does property verification work?', "Rentora doesn't run a manual verification step yet — every listing you see was published directly by its owner."),
    ('How do I schedule a property visit?', 'On a property page, tap "Schedule Visit" and pick a date and time. It\'s confirmed instantly — no owner approval needed.'),
    ('Is there any brokerage or hidden charges?', 'No. Rentora is a zero-brokerage platform — you deal directly with the owner.'),
    ('How can I save my favorite properties?', 'Tap the heart icon on any property card or the "Save Property" button on a listing page. Find them anytime under Saved Properties.'),
    ('What if my inquiry is not answered by the owner?', "Inquiries aren't gated by approval, so the owner's contact details are already visible — you can also try calling or WhatsApp-ing them directly."),
    ('How do I update my profile information?', 'Go to My Profile and click Edit Profile, or update individual sections from Settings.'),
    ('How do notifications work?', 'You get a notification whenever you send an inquiry, schedule a visit, or submit a support ticket. Manage channels under Settings > Notification Preferences.'),
]


def seed_faqs(apps, schema_editor):
    FAQ = apps.get_model('cms', 'FAQ')
    for order, (question, answer) in enumerate(CONTACT_FAQS):
        FAQ.objects.create(question=question, answer=answer, placement='contact', order=order)
    for order, (question, answer) in enumerate(TENANT_HELP_FAQS):
        FAQ.objects.create(question=question, answer=answer, placement='tenant_help', order=order)


def unseed_faqs(apps, schema_editor):
    FAQ = apps.get_model('cms', 'FAQ')
    all_questions = [q for q, _ in CONTACT_FAQS] + [q for q, _ in TENANT_HELP_FAQS]
    FAQ.objects.filter(question__in=all_questions).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_faqs, unseed_faqs),
    ]
