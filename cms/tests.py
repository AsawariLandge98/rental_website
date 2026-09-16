from django.test import TestCase

from .models import ContentBlock, FAQ, LegalPage, PageSEO, SiteSettings


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


class SiteSettingsSingletonTests(TestCase):
    def test_load_creates_a_row_if_none_exists(self):
        SiteSettings.objects.all().delete()
        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.pk, 1)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_save_always_forces_pk_1(self):
        settings_obj = SiteSettings(support_phone='+91 90000 00000')
        settings_obj.save()
        self.assertEqual(settings_obj.pk, 1)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_seed_migration_carried_forward_the_old_hardcoded_contact_info(self):
        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.support_phone, '+91 98765 43210')
        # The Feature 17 seed (0007) originally set 'support@rentora.local'
        # — a later migration (0012) swapped that placeholder, undeliverable
        # domain for a real inbox before go-live. This checks the final,
        # real value the app actually ships with today.
        self.assertEqual(settings_obj.support_email, 'rentora600@gmail.com')

    def test_default_platform_name_is_rentora(self):
        # The header/footer fall back to this when no admin has changed it —
        # confirms the default matches the brand name it replaced.
        self.assertEqual(SiteSettings.load().platform_name, 'Rentora')


class ContentBlockOrderingTests(TestCase):
    def test_blocks_order_within_a_placement(self):
        ContentBlock.objects.all().delete()
        ContentBlock.objects.create(placement=ContentBlock.Placement.HOME_WHY_CHOOSE, title='Second', order=2)
        ContentBlock.objects.create(placement=ContentBlock.Placement.HOME_WHY_CHOOSE, title='First', order=1)
        titles = list(ContentBlock.objects.filter(placement=ContentBlock.Placement.HOME_WHY_CHOOSE).values_list('title', flat=True))
        self.assertEqual(titles, ['First', 'Second'])

    def test_seed_migration_created_real_content_for_every_placement(self):
        for placement, _ in ContentBlock.Placement.choices:
            self.assertTrue(
                ContentBlock.objects.filter(placement=placement).exists(), f'No seeded blocks for {placement}',
            )


class LegalPageSeedTests(TestCase):
    def test_terms_and_privacy_exist_with_real_content(self):
        terms = LegalPage.objects.get(slug=LegalPage.Slug.TERMS)
        privacy = LegalPage.objects.get(slug=LegalPage.Slug.PRIVACY)
        self.assertTrue(len(terms.body) > 200)
        self.assertTrue(len(privacy.body) > 200)


class PageSEOSeedTests(TestCase):
    def test_every_real_public_page_has_a_seeded_seo_row(self):
        for page, _ in PageSEO.Page.choices:
            seo = PageSEO.objects.filter(page=page).first()
            self.assertIsNotNone(seo, f'No PageSEO row for {page}')
            self.assertTrue(seo.meta_title)
            self.assertTrue(seo.meta_description)

    def test_page_is_unique(self):
        with self.assertRaises(Exception):
            PageSEO.objects.create(page=PageSEO.Page.HOME, meta_title='Duplicate')
