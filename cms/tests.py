from django.test import TestCase

from .models import FAQ


class FAQPublicRenderingTests(TestCase):
    def setUp(self):
        FAQ.objects.create(
            question='Published contact FAQ', answer='Visible.', placement=FAQ.Placement.CONTACT, is_published=True,
        )
        FAQ.objects.create(
            question='Unpublished contact FAQ', answer='Hidden.', placement=FAQ.Placement.CONTACT, is_published=False,
        )
        FAQ.objects.create(
            question='Tenant help FAQ', answer='Only on help page.', placement=FAQ.Placement.TENANT_HELP, is_published=True,
        )

    def test_contact_page_shows_only_published_contact_faqs(self):
        response = self.client.get('/contact/')
        self.assertContains(response, 'Published contact FAQ')
        self.assertNotContains(response, 'Unpublished contact FAQ')
        self.assertNotContains(response, 'Tenant help FAQ')

    def test_seed_migration_created_real_faq_content(self):
        # The 0002_seed_faqs data migration should have populated real,
        # previously-hardcoded FAQ content — not left the table empty.
        self.assertTrue(FAQ.objects.filter(placement=FAQ.Placement.CONTACT).count() >= 5)
        self.assertTrue(FAQ.objects.filter(placement=FAQ.Placement.TENANT_HELP).count() >= 8)
