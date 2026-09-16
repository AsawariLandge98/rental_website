from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from cms.models import ContentBlock, PageSEO, SiteSettings
from properties.models import Property
from properties.views import get_city_options
from .models import City, ContactMessage, NewsletterSubscriber


class NewsletterTests(TestCase):
    def test_subscribe_creates_subscriber(self):
        response = self.client.post(reverse('core:subscribe_newsletter'), {'email': 'reader@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='reader@example.com').exists())

    def test_duplicate_email_rejected_gracefully(self):
        NewsletterSubscriber.objects.create(email='reader@example.com')
        response = self.client.post(reverse('core:subscribe_newsletter'), {'email': 'reader@example.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(NewsletterSubscriber.objects.filter(email='reader@example.com').count(), 1)

    def test_invalid_email_rejected(self):
        response = self.client.post(reverse('core:subscribe_newsletter'), {'email': 'not-an-email'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(NewsletterSubscriber.objects.exists())


class ContactFormTests(TestCase):
    def test_valid_submission_creates_message(self):
        response = self.client.post(reverse('core:contact'), {
            'name': 'Test User', 'email': 'test@example.com', 'phone': '9876543210',
            'subject': 'Question', 'message': 'How does this work?',
        })
        self.assertRedirects(response, reverse('core:contact'))
        self.assertTrue(ContactMessage.objects.filter(email='test@example.com').exists())

    def test_missing_required_fields_does_not_create_message(self):
        response = self.client.post(reverse('core:contact'), {'name': '', 'email': '', 'message': ''})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ContactMessage.objects.exists())


class HomePageTests(TestCase):
    def test_shows_empty_state_with_no_published_properties(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'No listings yet')

    def test_shows_real_published_property(self):
        owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        Property.objects.create(
            owner=owner, title='Real Listing', status=Property.Status.PUBLISHED,
            city='Pune', monthly_rent=20000,
        )
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Real Listing')
        self.assertNotContains(response, 'No listings yet')

    def test_quick_search_submits_to_real_search_page(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, f'action="{reverse("properties:search")}"')

    def test_no_fake_testimonials(self):
        response = self.client.get(reverse('core:home'))
        self.assertNotContains(response, 'What Our Users Say')


class CmsContentBlockRenderingTests(TestCase):
    """Home/About/Become a Host used to render hardcoded Python lists —
    confirms they now render real, admin-editable ContentBlock rows, and
    that unpublished blocks are correctly hidden."""

    def test_home_shows_published_why_choose_block(self):
        ContentBlock.objects.create(
            placement=ContentBlock.Placement.HOME_WHY_CHOOSE, title='Real Why-Choose Item', is_published=True,
        )
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'Real Why-Choose Item')

    def test_unpublished_block_is_hidden(self):
        ContentBlock.objects.create(
            placement=ContentBlock.Placement.HOME_WHY_CHOOSE, title='Draft Item', is_published=False,
        )
        response = self.client.get(reverse('core:home'))
        self.assertNotContains(response, 'Draft Item')

    def test_about_shows_published_blocks(self):
        ContentBlock.objects.create(placement=ContentBlock.Placement.ABOUT_VALUES, title='Real Value')
        ContentBlock.objects.create(placement=ContentBlock.Placement.ABOUT_WHY_CHOOSE, title='Real Why Choose')
        response = self.client.get(reverse('core:about'))
        self.assertContains(response, 'Real Value')
        self.assertContains(response, 'Real Why Choose')

    def test_become_host_shows_published_blocks(self):
        ContentBlock.objects.create(placement=ContentBlock.Placement.HOST_STEPS, title='Real Step')
        ContentBlock.objects.create(placement=ContentBlock.Placement.HOST_PERKS, title='Real Perk')
        response = self.client.get(reverse('core:become_host'))
        self.assertContains(response, 'Real Step')
        self.assertContains(response, 'Real Perk')


class LegalPageTests(TestCase):
    def test_terms_page_renders_real_content(self):
        response = self.client.get(reverse('core:legal_page', args=['terms']))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terms')

    def test_privacy_page_renders_real_content(self):
        response = self.client.get(reverse('core:legal_page', args=['privacy']))
        self.assertEqual(response.status_code, 200)

    def test_unknown_slug_404s(self):
        response = self.client.get(reverse('core:legal_page', args=['bogus']))
        self.assertEqual(response.status_code, 404)

    def test_footer_links_to_real_legal_pages(self):
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, reverse('core:legal_page', args=['terms']))
        self.assertContains(response, reverse('core:legal_page', args=['privacy']))


class SiteSettingsContextTests(TestCase):
    def test_site_settings_available_sitewide(self):
        response = self.client.get(reverse('core:home'))
        self.assertIn('site_settings', response.context)

    def test_platform_name_renders_in_header_and_footer(self):
        settings_obj = SiteSettings.load()
        settings_obj.platform_name = 'TestBrand'
        settings_obj.save()
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'TestBrand')

    def test_analytics_script_only_renders_when_id_is_set(self):
        response = self.client.get(reverse('core:home'))
        self.assertNotContains(response, 'googletagmanager.com/gtag/js')

        settings_obj = SiteSettings.load()
        settings_obj.google_analytics_id = 'G-TESTID123'
        settings_obj.save()
        response = self.client.get(reverse('core:home'))
        self.assertContains(response, 'G-TESTID123')


class PageSeoRenderingTests(TestCase):
    """Real per-page <title>/<meta description>, sourced from PageSEO —
    falls back to the page's existing hardcoded default when a row has no
    override set."""

    def test_real_meta_description_renders_from_seed_data(self):
        response = self.client.get(reverse('core:home'))
        seo = PageSEO.objects.get(page=PageSEO.Page.HOME)
        self.assertContains(response, f'<meta name="description" content="{seo.meta_description}">')

    def test_custom_meta_title_overrides_the_page_default(self):
        seo = PageSEO.objects.get(page=PageSEO.Page.ABOUT)
        seo.meta_title = 'Custom About Title'
        seo.save()
        response = self.client.get(reverse('core:about'))
        self.assertContains(response, '<title>Custom About Title</title>')

    def test_no_meta_description_tag_when_blank(self):
        seo = PageSEO.objects.get(page=PageSEO.Page.CONTACT)
        seo.meta_description = ''
        seo.save()
        response = self.client.get(reverse('core:contact'))
        self.assertNotContains(response, '<meta name="description"')


class SitemapTests(TestCase):
    def test_sitemap_is_reachable_and_lists_static_pages(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('core:home'))
        self.assertContains(response, reverse('core:about'))

    def test_sitemap_lists_only_published_properties(self):
        owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.OWNER,
        )
        published = Property.objects.create(owner=owner, status=Property.Status.PUBLISHED, title='Live Listing')
        draft = Property.objects.create(owner=owner, status=Property.Status.DRAFT, title='Draft Listing')
        response = self.client.get('/sitemap.xml')
        self.assertContains(response, reverse('properties:detail', args=[published.pk]))
        self.assertNotContains(response, reverse('properties:detail', args=[draft.pk]))


class CityOptionsTests(TestCase):
    """Feature 25 — the search/quick-search city dropdown is now backed by
    a real, admin-manageable core.City model instead of a hardcoded list
    (properties/views.py::CITY_OPTIONS used to be
    ['Bengaluru', 'Hyderabad', 'Mumbai', 'Pune'])."""

    def test_seed_migration_carried_forward_the_old_hardcoded_cities(self):
        names = list(City.objects.order_by('order').values_list('name', flat=True))
        self.assertEqual(names, ['Bengaluru', 'Hyderabad', 'Mumbai', 'Pune'])

    def test_get_city_options_only_returns_active_cities_in_order(self):
        City.objects.all().delete()
        City.objects.create(name='Chennai', order=2)
        City.objects.create(name='Delhi', order=1)
        City.objects.create(name='Inactive City', order=0, is_active=False)
        self.assertEqual(get_city_options(), ['Delhi', 'Chennai'])

    def test_search_page_offers_the_real_city_list(self):
        City.objects.all().delete()
        City.objects.create(name='Jaipur', order=0)
        response = self.client.get(reverse('properties:search'))
        self.assertContains(response, 'Jaipur')

    def test_property_can_still_be_listed_in_a_city_not_in_the_curated_list(self):
        # City is a dropdown shortcut only — Property.city stays free text,
        # so an owner isn't blocked from a city that isn't curated yet.
        owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.OWNER,
        )
        prop = Property.objects.create(
            owner=owner, status=Property.Status.PUBLISHED, title='Listing', city='Nowhereville',
        )
        self.assertNotIn('Nowhereville', get_city_options())
        response = self.client.get(reverse('properties:detail', args=[prop.pk]))
        self.assertContains(response, 'Nowhereville')


class AdminCityManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='StrongPass123', full_name='Admin', role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)

    def test_add_new_city_makes_it_available_immediately(self):
        response = self.client.post(reverse('dashboard:admin_city_add'), {'name': 'Jaipur', 'order': 10, 'is_active': 'on'})
        self.assertRedirects(response, reverse('dashboard:admin_cities'))
        self.assertTrue(City.objects.filter(name='Jaipur', is_active=True).exists())
        self.assertIn('Jaipur', get_city_options())

    def test_deactivating_a_city_removes_it_from_the_dropdown_without_deleting_it(self):
        city = City.objects.get(name='Pune')
        response = self.client.post(reverse('dashboard:admin_city_toggle', args=[city.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_cities'))
        city.refresh_from_db()
        self.assertFalse(city.is_active)
        self.assertNotIn('Pune', get_city_options())

    def test_delete_removes_the_city(self):
        city = City.objects.get(name='Mumbai')
        response = self.client.post(reverse('dashboard:admin_city_delete', args=[city.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_cities'))
        self.assertFalse(City.objects.filter(pk=city.pk).exists())

    def test_non_admin_cannot_manage_cities(self):
        tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(tenant)
        response = self.client.get(reverse('dashboard:admin_cities'))
        self.assertEqual(response.status_code, 403)
