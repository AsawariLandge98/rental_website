from django.db import migrations

# Property visits now require owner approval (see visits.Visit.Status.PENDING)
# instead of being confirmed the instant a tenant books one — these 2 FAQ
# answers said "confirmed instantly / no approval needed" and are no longer
# true. Fixed in place via a forward data migration rather than editing the
# 0002 seed migration's history, since these rows are already live data.
FIXES = {
    'Can I schedule a visit before finalizing?':
        "Yes — request a visit slot directly from the property detail page. The owner will confirm or decline it.",
    'How do I schedule a property visit?':
        'On a property page, tap "Schedule Visit" and pick a date and time. The owner will review your request and '
        'confirm or decline it.',
}


def apply_fixes(apps, schema_editor):
    FAQ = apps.get_model('cms', 'FAQ')
    for question, answer in FIXES.items():
        FAQ.objects.filter(question=question).update(answer=answer)


def revert_fixes(apps, schema_editor):
    # Not reversible to the old (now-inaccurate) wording on purpose.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0002_seed_faqs'),
    ]

    operations = [
        migrations.RunPython(apply_fixes, revert_fixes),
    ]
