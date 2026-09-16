from django.db import migrations

# Real starter copy, not lorem-ipsum placeholders — describes what the site
# actually does today (direct owner/tenant contact, zero brokerage, real
# Razorpay test-mode subscription payments, what account data is collected).
# It's a reasonable draft an admin can edit from CMS > Legal Pages; it is
# NOT legal advice and hasn't been reviewed by a lawyer.

TERMS_BODY = """Welcome to Rentora. By creating an account or using this website, you agree to these Terms & Conditions.

1. What Rentora is
Rentora is a zero-brokerage platform that lets property owners list rentals directly and lets tenants search, save and contact owners directly. Rentora does not act as a broker, does not take a cut of your rent, and is not a party to any rental agreement between a tenant and an owner.

2. Your account
You must provide accurate information when you register (name, email, mobile number) and are responsible for keeping your login credentials secure. You may register as a Tenant, a Property Owner, or a Hotel/Homestay Owner.

3. Listings
Owners are solely responsible for the accuracy of the properties they list — title, price, photos, location and availability. Rentora does not verify listings before they go live.

4. Contacting owners and scheduling visits
Tenants may contact owners directly (call, message, email) and request property visits through the platform. Any agreement reached — rent, deposit, move-in date — is between the tenant and the owner; Rentora is not responsible for it.

5. Subscriptions and payments
Property owners may subscribe to a paid listing plan. Payments are processed through Razorpay. Subscription fees are for platform features (like listing limits) — they are not brokerage and are unrelated to any rent paid between tenant and owner.

6. Acceptable use
You agree not to post false listings, impersonate another person, or use the platform for anything unlawful. We may suspend or deactivate accounts that violate these terms.

7. Changes to these terms
We may update these terms from time to time. Continued use of the site after a change means you accept the updated terms.

8. Contact
Questions about these terms can be raised through Help & Support or the Contact page."""

PRIVACY_BODY = """This Privacy Policy explains what information Rentora collects and how it's used.

1. Information we collect
When you register, we collect your name, email address, mobile number and the account role you choose (Tenant, Owner, or Hotel/Homestay Owner). If you complete your profile, you may also provide details like date of birth, occupation, or rental preferences. Property owners provide listing details and photos when they publish a property.

2. How we use your information
We use your information to run your account, show your listings or saved properties, let tenants and owners contact each other, send you notifications about inquiries, visits and support tickets, and process subscription payments through Razorpay.

3. What we share
Your contact details are shown to the other party in an inquiry or visit request you're involved in (for example, an owner can see the tenant's name when they receive an inquiry). We do not sell your personal information to third parties.

4. Payments
Subscription payments are processed by Razorpay. Rentora does not store your card or payment credentials — Razorpay handles that directly.

5. Cookies and sessions
We use standard session cookies to keep you signed in. We don't use third-party advertising trackers.

6. Your choices
You can update or correct your profile information at any time from Settings. You can deactivate your account from Settings — this signs you out and deactivates your account; contact support if you want your data fully removed.

7. Changes to this policy
We may update this policy from time to time. Continued use of the site after a change means you accept the updated policy.

8. Contact
Questions about this policy can be raised through Help & Support or the Contact page."""


def seed_legal_pages(apps, schema_editor):
    LegalPage = apps.get_model('cms', 'LegalPage')
    LegalPage.objects.get_or_create(
        slug='terms', defaults={'title': 'Terms & Conditions', 'body': TERMS_BODY},
    )
    LegalPage.objects.get_or_create(
        slug='privacy', defaults={'title': 'Privacy Policy', 'body': PRIVACY_BODY},
    )


def unseed_legal_pages(apps, schema_editor):
    LegalPage = apps.get_model('cms', 'LegalPage')
    LegalPage.objects.filter(slug__in=['terms', 'privacy']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0005_seed_content_blocks'),
    ]

    operations = [
        migrations.RunPython(seed_legal_pages, unseed_legal_pages),
    ]
