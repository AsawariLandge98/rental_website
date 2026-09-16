import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from cms.models import SiteSettings
from .models import Amenity, Property, PropertyPhoto, SavedProperty

# A minimal valid 1x1 GIF, so Pillow (used by ImageField validation) accepts it.
TINY_GIF = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def make_photo():
    return SimpleUploadedFile('test.gif', TINY_GIF, content_type='image/gif')


MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PropertyModelTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )

    def test_missing_publish_requirements_lists_everything_missing(self):
        prop = Property.objects.create(owner=self.owner, category=Property.Category.RESIDENTIAL)
        missing = prop.missing_publish_requirements()
        self.assertIn('Property Title', missing)
        self.assertIn('Monthly Rent', missing)
        self.assertIn('At least 5 photos (currently 0)', missing)
        self.assertFalse(prop.can_publish)

    def test_can_publish_once_complete(self):
        prop = Property.objects.create(
            owner=self.owner, category=Property.Category.RESIDENTIAL,
            title='2BHK Flat', description='Nice flat', property_type=Property.PropertyType.APARTMENT,
            city='Bengaluru', area_locality='Koramangala', monthly_rent=20000,
        )
        for i in range(5):
            PropertyPhoto.objects.create(property=prop, image=make_photo(), order=i)
        self.assertEqual(prop.missing_publish_requirements(), [])
        self.assertTrue(prop.can_publish)

    def test_min_photos_to_publish_is_a_real_admin_setting_not_hardcoded(self):
        # Super Admin can change the minimum from System Settings — confirms
        # this reads SiteSettings live rather than a hardcoded constant.
        settings_obj = SiteSettings.load()
        settings_obj.min_photos_to_publish = 2
        settings_obj.save()

        prop = Property.objects.create(
            owner=self.owner, category=Property.Category.RESIDENTIAL,
            title='Studio', description='Cozy studio', property_type=Property.PropertyType.APARTMENT,
            city='Bengaluru', area_locality='Koramangala', monthly_rent=15000,
        )
        for i in range(2):
            PropertyPhoto.objects.create(property=prop, image=make_photo(), order=i)
        self.assertEqual(prop.missing_publish_requirements(), [])
        self.assertTrue(prop.can_publish)

    def test_badge_reflects_listing_plan_not_verification(self):
        prop = Property.objects.create(owner=self.owner, listing_plan=Property.ListingPlan.PREMIUM)
        self.assertEqual(prop.badge, 'premium')
        prop.listing_plan = Property.ListingPlan.GOLD
        self.assertEqual(prop.badge, 'featured')
        prop.listing_plan = Property.ListingPlan.FREE
        self.assertIsNone(prop.badge)

    def test_cover_photo_falls_back_to_first_photo(self):
        prop = Property.objects.create(owner=self.owner)
        p1 = PropertyPhoto.objects.create(property=prop, image=make_photo(), order=0)
        self.assertEqual(prop.cover_photo, p1)
        p2 = PropertyPhoto.objects.create(property=prop, image=make_photo(), order=1, is_cover=True)
        self.assertEqual(prop.cover_photo, p2)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ListingWizardTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.login(email='owner@example.com', password='StrongPass123')

    def test_anonymous_user_is_redirected_to_login(self):
        self.client.logout()
        response = self.client.get('/properties/manage/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_tenant_cannot_access_listing_management(self):
        self.client.logout()
        self.client.login(email='tenant@example.com', password='StrongPass123')
        response = self.client.get('/properties/manage/')
        self.assertEqual(response.status_code, 403)

    def test_start_listing_blocks_once_owner_reaches_their_plan_limit(self):
        # The seeded Free plan (no subscription needed) caps at 3 listings.
        for i in range(3):
            Property.objects.create(owner=self.owner, title=f'Listing {i}')
        response = self.client.get('/properties/manage/new/')
        self.assertRedirects(response, '/owner/dashboard/subscription/')
        self.assertEqual(self.owner.properties.count(), 3)

        response = self.client.post('/properties/manage/new/', {'category': 'residential'})
        self.assertRedirects(response, '/owner/dashboard/subscription/')
        self.assertEqual(self.owner.properties.count(), 3)

    def test_full_wizard_flow_creates_publishable_listing(self):
        response = self.client.post('/properties/manage/new/', {'category': 'residential'})
        self.assertEqual(response.status_code, 302)
        prop = Property.objects.get(owner=self.owner)
        self.assertEqual(prop.status, Property.Status.DRAFT)

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/property-info/', {
            'title': '2 BHK Flat in Koramangala',
            'description': 'Spacious and well ventilated.',
            'property_type': 'apartment',
            'furnishing_status': 'fully_furnished',
            'property_age': '1_3',
            'total_area': 1200, 'carpet_area': 1100, 'built_up_area': 1150,
            'facing': 'north', 'floor_number': 2, 'total_floors': 5,
            'bedrooms': 2, 'bathrooms': 2, 'balconies': 1, 'parking': 'car',
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/location/')

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/location/', {
            'state': 'Karnataka', 'district': 'Bengaluru Urban', 'city': 'Bengaluru',
            'area_locality': 'Koramangala', 'landmark': 'Near Forum Mall',
            'pincode': '560034', 'full_address': '123, 4th Block',
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/preferences/')

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/preferences/', {
            'tenant_preferences': ['family', 'professionals'],
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/rent/')

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/rent/', {
            'monthly_rent': 24000, 'security_deposit': 48000, 'maintenance_charges': 2000,
            'electricity_charges': 'As per meter', 'water_charges': 'Included', 'no_brokerage': 'on',
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/availability/')

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/availability/', {
            'available_from': '2026-09-01', 'minimum_stay': '6_months', 'lease_duration': '1_year',
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/amenities/')

        amenity_ids = list(Amenity.objects.filter(name__in=['Wi-Fi', 'Lift']).values_list('id', flat=True))
        response = self.client.post(f'/properties/manage/{prop.pk}/edit/amenities/', {'amenities': amenity_ids})
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/photos/')

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/photos/', {
            'images': [make_photo() for _ in range(5)],
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/edit/photos/')
        prop.refresh_from_db()
        self.assertEqual(prop.photos.count(), 5)
        self.assertTrue(prop.photos.filter(is_cover=True).exists())

        response = self.client.post(f'/properties/manage/{prop.pk}/edit/contact/', {
            'contact_preferences': ['chat', 'whatsapp'],
        })
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/preview/')

        prop.refresh_from_db()
        self.assertEqual(prop.missing_publish_requirements(), [])
        self.assertCountEqual(prop.tenant_preferences, ['family', 'professionals'])
        self.assertCountEqual(prop.contact_preferences, ['chat', 'whatsapp'])
        self.assertEqual(prop.amenities.count(), 2)

        response = self.client.post(f'/properties/manage/{prop.pk}/publish/')
        self.assertRedirects(response, '/properties/manage/')
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.Status.PUBLISHED)
        self.assertIsNotNone(prop.published_at)

    def test_cannot_publish_incomplete_listing(self):
        prop = Property.objects.create(owner=self.owner, title='Incomplete listing')
        response = self.client.post(f'/properties/manage/{prop.pk}/publish/')
        self.assertRedirects(response, f'/properties/manage/{prop.pk}/preview/')
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.Status.DRAFT)

    def test_photo_upload_respects_max_limit(self):
        prop = Property.objects.create(owner=self.owner)
        PropertyPhoto.objects.bulk_create([
            PropertyPhoto(property=prop, image=make_photo(), order=i) for i in range(24)
        ])
        response = self.client.post(f'/properties/manage/{prop.pk}/edit/photos/', {
            'images': [make_photo(), make_photo()],
        })
        self.assertEqual(response.status_code, 302)
        prop.refresh_from_db()
        self.assertEqual(prop.photos.count(), 24, 'only 1 slot was free, upload of 2 should have been rejected')

    def test_set_cover_and_delete_photo(self):
        prop = Property.objects.create(owner=self.owner)
        p1 = PropertyPhoto.objects.create(property=prop, image=make_photo(), order=0, is_cover=True)
        p2 = PropertyPhoto.objects.create(property=prop, image=make_photo(), order=1)

        self.client.post(f'/properties/manage/{prop.pk}/photos/{p2.id}/cover/')
        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertFalse(p1.is_cover)
        self.assertTrue(p2.is_cover)

        self.client.post(f'/properties/manage/{prop.pk}/photos/{p1.id}/delete/')
        self.assertEqual(prop.photos.count(), 1)

    def test_owner_cannot_edit_another_owners_listing(self):
        other_owner = User.objects.create_user(
            email='other@example.com', password='StrongPass123',
            full_name='Other Owner', role=User.Role.OWNER,
        )
        other_prop = Property.objects.create(owner=other_owner, title='Not yours')
        response = self.client.get(f'/properties/manage/{other_prop.pk}/edit/property-info/')
        self.assertEqual(response.status_code, 404)

    def test_my_listings_only_shows_own_properties(self):
        Property.objects.create(owner=self.owner, title='Mine')
        other_owner = User.objects.create_user(
            email='other@example.com', password='StrongPass123',
            full_name='Other Owner', role=User.Role.OWNER,
        )
        Property.objects.create(owner=other_owner, title='Not mine')
        response = self.client.get('/properties/manage/')
        self.assertContains(response, 'Mine')
        self.assertNotContains(response, 'Not mine')

    def test_status_transitions_pause_resume_archive(self):
        prop = Property.objects.create(
            owner=self.owner, title='T', description='D', property_type='apartment',
            city='Bengaluru', area_locality='Koramangala', monthly_rent=10000,
            status=Property.Status.PUBLISHED,
        )
        for i in range(5):
            PropertyPhoto.objects.create(property=prop, image=make_photo(), order=i)

        self.client.post(f'/properties/manage/{prop.pk}/status/paused/')
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.Status.PAUSED)

        self.client.post(f'/properties/manage/{prop.pk}/status/published/')
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.Status.PUBLISHED)

        self.client.post(f'/properties/manage/{prop.pk}/status/archived/')
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.Status.ARCHIVED)

    def test_delete_listing_removes_it(self):
        prop = Property.objects.create(owner=self.owner, title='Delete me')
        response = self.client.post(f'/properties/manage/{prop.pk}/delete/')
        self.assertRedirects(response, '/properties/manage/')
        self.assertFalse(Property.objects.filter(pk=prop.pk).exists())

    def test_republishing_a_rejected_listing_clears_the_rejection_reason(self):
        prop = Property.objects.create(
            owner=self.owner, title='T', description='D', property_type='apartment',
            city='Bengaluru', area_locality='Koramangala', monthly_rent=10000,
            status=Property.Status.DRAFT, rejection_reason='Photos were blurry.',
        )
        for i in range(5):
            PropertyPhoto.objects.create(property=prop, image=make_photo(), order=i)

        self.client.post(f'/properties/manage/{prop.pk}/status/published/')
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.Status.PUBLISHED)
        self.assertEqual(prop.rejection_reason, '')

    def test_my_listings_shows_rejection_banner(self):
        Property.objects.create(owner=self.owner, title='Rejected One', rejection_reason='Fix the price.')
        response = self.client.get('/properties/manage/')
        self.assertContains(response, 'Rejected by admin')
        self.assertContains(response, 'Fix the price.')


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PublicVisibilityTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )

    def _complete_property(self, **overrides):
        defaults = dict(
            owner=self.owner, title='2 BHK Flat', description='Nice place',
            property_type='apartment', city='Bengaluru', area_locality='Koramangala',
            monthly_rent=20000, status=Property.Status.PUBLISHED,
        )
        defaults.update(overrides)
        prop = Property.objects.create(**defaults)
        for i in range(5):
            PropertyPhoto.objects.create(property=prop, image=make_photo(), order=i, is_cover=(i == 0))
        return prop

    def test_published_property_visible_on_search_and_detail(self):
        prop = self._complete_property()
        response = self.client.get('/properties/')
        self.assertContains(response, '2 BHK Flat')

        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2 BHK Flat')
        self.assertContains(response, 'Nice place')

    def test_draft_property_hidden_from_public(self):
        prop = Property.objects.create(owner=self.owner, title='Secret draft', status=Property.Status.DRAFT)
        response = self.client.get('/properties/')
        self.assertNotContains(response, 'Secret draft')
        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertEqual(response.status_code, 404)

    def test_paused_and_archived_properties_hidden_from_public(self):
        paused = self._complete_property(title='Paused listing', status=Property.Status.PAUSED)
        archived = self._complete_property(title='Archived listing', status=Property.Status.ARCHIVED)
        response = self.client.get('/properties/')
        self.assertNotContains(response, 'Paused listing')
        self.assertNotContains(response, 'Archived listing')
        self.assertEqual(self.client.get(f'/properties/{paused.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/properties/{archived.pk}/').status_code, 404)

    def test_search_filters_by_city_and_property_type_and_budget(self):
        self._complete_property(title='Bengaluru Flat', city='Bengaluru', monthly_rent=20000)
        self._complete_property(title='Pune Flat', city='Pune', monthly_rent=20000)

        response = self.client.get('/properties/', {'city': 'Bengaluru'})
        self.assertContains(response, 'Bengaluru Flat')
        self.assertNotContains(response, 'Pune Flat')

        response = self.client.get('/properties/', {'budget': '0-15000'})
        self.assertNotContains(response, 'Bengaluru Flat')
        self.assertNotContains(response, 'Pune Flat')

    def test_no_verification_badge_ever_shown(self):
        prop = self._complete_property(listing_plan=Property.ListingPlan.PREMIUM)
        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertNotContains(response, 'Verified Property')
        self.assertContains(response, 'Premium')


class SearchAdvancedFiltersTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )

    def _prop(self, **overrides):
        defaults = dict(
            owner=self.owner, title='Listing', status=Property.Status.PUBLISHED,
            city='Bengaluru', monthly_rent=20000,
        )
        defaults.update(overrides)
        return Property.objects.create(**defaults)

    def test_property_type_checkboxes_filter_with_or_across_multiple_values(self):
        self._prop(title='Villa Listing', property_type=Property.PropertyType.VILLA)
        self._prop(title='Room Listing', property_type=Property.PropertyType.ROOM)
        self._prop(title='Apartment Listing', property_type=Property.PropertyType.APARTMENT)

        response = self.client.get('/properties/', {'property_type': ['villa', 'room']})
        self.assertContains(response, 'Villa Listing')
        self.assertContains(response, 'Room Listing')
        self.assertNotContains(response, 'Apartment Listing')

    def test_bedrooms_studio_and_4plus_filters(self):
        self._prop(title='Studio Listing', property_type=Property.PropertyType.STUDIO, bedrooms=0)
        self._prop(title='2BHK Listing', bedrooms=2)
        self._prop(title='5BHK Listing', bedrooms=5)

        response = self.client.get('/properties/', {'bedrooms': 'studio'})
        self.assertContains(response, 'Studio Listing')
        self.assertNotContains(response, '2BHK Listing')

        response = self.client.get('/properties/', {'bedrooms': '4plus'})
        self.assertContains(response, '5BHK Listing')
        self.assertNotContains(response, '2BHK Listing')

    def test_furnishing_filter_matches_real_choices(self):
        self._prop(title='Furnished Listing', furnishing_status=Property.FurnishingStatus.FULLY_FURNISHED)
        self._prop(title='Unfurnished Listing', furnishing_status=Property.FurnishingStatus.UNFURNISHED)

        response = self.client.get('/properties/', {'furnishing': 'fully_furnished'})
        self.assertContains(response, 'Furnished Listing')
        self.assertNotContains(response, 'Unfurnished Listing')

    def test_price_slider_range_filters_and_defaults_are_a_no_op(self):
        self._prop(title='Cheap Listing', monthly_rent=5000)
        self._prop(title='Expensive Listing', monthly_rent=95000)

        response = self.client.get('/properties/', {'price_min': '0', 'price_max': '100000'})
        self.assertContains(response, 'Cheap Listing')
        self.assertContains(response, 'Expensive Listing')

        response = self.client.get('/properties/', {'price_min': '50000', 'price_max': '100000'})
        self.assertNotContains(response, 'Cheap Listing')
        self.assertContains(response, 'Expensive Listing')


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class OwnerContactTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Test Owner',
            role=User.Role.OWNER, mobile_number='9876543210',
        )

    def _published_property(self, **overrides):
        defaults = dict(
            owner=self.owner, title='Contact Me Flat', description='Nice place',
            property_type='apartment', city='Bengaluru', area_locality='Koramangala',
            monthly_rent=20000, status=Property.Status.PUBLISHED,
        )
        defaults.update(overrides)
        prop = Property.objects.create(**defaults)
        for i in range(5):
            PropertyPhoto.objects.create(property=prop, image=make_photo(), order=i)
        return prop

    def test_contact_details_visible_without_any_inquiry(self):
        prop = self._published_property(contact_preferences=['call', 'whatsapp', 'email'])
        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertContains(response, 'tel:+919876543210')
        self.assertContains(response, 'https://wa.me/919876543210')
        self.assertContains(response, 'mailto:owner@example.com')
        self.assertNotContains(response, 'inquiry is approved')
        self.assertNotContains(response, 'Contact details will be shared')

    def test_only_selected_contact_channels_shown(self):
        prop = self._published_property(contact_preferences=['email'])
        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertContains(response, 'mailto:owner@example.com')
        self.assertNotContains(response, 'tel:+919876543210')
        self.assertNotContains(response, 'https://wa.me/919876543210')

    def test_empty_preferences_falls_back_to_all_channels(self):
        prop = self._published_property(contact_preferences=[])
        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertContains(response, 'tel:+919876543210')
        self.assertContains(response, 'https://wa.me/919876543210')
        self.assertContains(response, 'mailto:owner@example.com')

    def test_contact_owner_button_present_when_channels_available(self):
        prop = self._published_property()
        response = self.client.get(f'/properties/{prop.pk}/')
        self.assertContains(response, 'js-contact-trigger')
        self.assertContains(response, 'id="contactSheet"')


class PropertyReviewsDisplayTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.property = Property.objects.create(
            owner=self.owner, title='2BHK Flat', status=Property.Status.PUBLISHED,
            city='Nagpur', monthly_rent=15000,
        )

    def test_no_reviews_shows_honest_empty_state(self):
        response = self.client.get(f'/properties/{self.property.pk}/')
        self.assertContains(response, 'No reviews yet')
        self.assertEqual(response.context['review_count'], 0)

    def test_real_review_and_average_render(self):
        from reviews.models import Review
        Review.objects.create(tenant=self.tenant, property=self.property, rating=4, comment='Really liked it here.')
        response = self.client.get(f'/properties/{self.property.pk}/')
        self.assertContains(response, 'Really liked it here.')
        self.assertContains(response, 'Test Tenant')
        self.assertEqual(response.context['review_count'], 1)
        self.assertEqual(response.context['review_average'], 4)

    def test_write_review_form_only_shown_after_completed_visit(self):
        from visits.models import Visit
        response = self.client.get(f'/properties/{self.property.pk}/')
        self.assertFalse(response.context['can_review'])

        self.client.force_login(self.tenant)
        response = self.client.get(f'/properties/{self.property.pk}/')
        self.assertFalse(response.context['can_review'])
        self.assertContains(response, 'Complete a visit to this property to leave a review.')

        Visit.objects.create(
            tenant=self.tenant, property=self.property,
            scheduled_at=timezone.now() - timezone.timedelta(days=1), status=Visit.Status.COMPLETED,
        )
        response = self.client.get(f'/properties/{self.property.pk}/')
        self.assertTrue(response.context['can_review'])
        self.assertContains(response, 'Write a Review')


class SavedPropertyTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.property = Property.objects.create(
            owner=self.owner, title='2BHK Flat', status=Property.Status.PUBLISHED,
            city='Nagpur', monthly_rent=15000,
        )

    def test_toggle_saves_then_unsaves(self):
        self.client.force_login(self.tenant)
        url = f'/properties/{self.property.pk}/save/'
        self.client.post(url)
        self.assertTrue(SavedProperty.objects.filter(tenant=self.tenant, property=self.property).exists())
        self.client.post(url)
        self.assertFalse(SavedProperty.objects.filter(tenant=self.tenant, property=self.property).exists())

    def test_search_results_reflects_saved_state(self):
        SavedProperty.objects.create(tenant=self.tenant, property=self.property)
        self.client.force_login(self.tenant)
        response = self.client.get('/properties/')
        self.assertContains(response, 'is-saved')

    def test_owner_cannot_save_property(self):
        self.client.force_login(self.owner)
        response = self.client.post(f'/properties/{self.property.pk}/save/')
        self.assertEqual(response.status_code, 403)


class SearchPaginationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        for i in range(15):
            Property.objects.create(
                owner=self.owner, title=f'Property {i}', status=Property.Status.PUBLISHED,
                city='Nagpur', monthly_rent=10000 + i * 1000,
            )

    def test_default_page_shows_first_12(self):
        response = self.client.get('/properties/')
        self.assertEqual(len(response.context['properties']), 12)
        self.assertEqual(response.context['result_count'], 15)

    def test_second_page_shows_remainder(self):
        response = self.client.get('/properties/?page=2')
        self.assertEqual(len(response.context['properties']), 3)

    def test_per_page_override(self):
        response = self.client.get('/properties/?per_page=24')
        self.assertEqual(len(response.context['properties']), 15)

    def test_sort_by_price_ascending(self):
        response = self.client.get('/properties/?sort=price_asc')
        prices = [p['price'] for p in response.context['properties']]
        self.assertEqual(prices, sorted(prices))

    def test_empty_state_when_no_results(self):
        response = self.client.get('/properties/?city=NoSuchCity')
        self.assertContains(response, 'No properties match your search')


class PropertyDetailBookingUiTests(TestCase):
    """Feature 26 — property_detail.html shows a real "Request to Book"
    flow for bookable listings (Hotel/Guest House/Homestay) instead of the
    regular-rental "Schedule Visit" button."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.hotel = Property.objects.create(
            owner=self.owner, title='Lakeview Homestay', status=Property.Status.PUBLISHED,
            category=Property.Category.HOMESTAY, city='Nagpur', nightly_rate=2000,
        )
        self.rental = Property.objects.create(
            owner=self.owner, title='2BHK Flat', status=Property.Status.PUBLISHED,
            category=Property.Category.RESIDENTIAL, city='Nagpur', monthly_rent=15000,
        )
        self.client.force_login(self.tenant)

    def test_bookable_property_shows_request_to_book_not_schedule_visit(self):
        response = self.client.get(f'/properties/{self.hotel.pk}/')
        self.assertContains(response, 'Request to Book')
        self.assertContains(response, 'js-booking-trigger')
        self.assertNotContains(response, 'js-visit-trigger')

    def test_regular_rental_still_shows_schedule_visit_not_booking(self):
        response = self.client.get(f'/properties/{self.rental.pk}/')
        self.assertContains(response, 'Schedule Visit')
        self.assertContains(response, 'js-visit-trigger')
        self.assertNotContains(response, 'js-booking-trigger')

    def test_bookable_property_context_flag_is_true(self):
        response = self.client.get(f'/properties/{self.hotel.pk}/')
        self.assertTrue(response.context['property']['is_bookable'])


class RatingBadgeOnCardsTests(TestCase):
    """Feature 26 — a real average-rating badge on property/hotel/search
    grid cards, annotated at the queryset level (properties/views.py::
    _with_rating) to avoid an N+1 query per card. Deliberately deferred out
    of Feature 23 (Reviews) for exactly this reason; built now."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Tenant', role=User.Role.TENANT,
        )
        self.other_tenant = User.objects.create_user(
            email='tenant2@example.com', password='StrongPass123', full_name='Tenant Two', role=User.Role.TENANT,
        )
        self.reviewed = Property.objects.create(
            owner=self.owner, title='Reviewed Flat', status=Property.Status.PUBLISHED,
            city='Bengaluru', monthly_rent=20000,
        )
        self.unreviewed = Property.objects.create(
            owner=self.owner, title='Unreviewed Flat', status=Property.Status.PUBLISHED,
            city='Bengaluru', monthly_rent=18000,
        )

    def test_search_results_show_a_real_rating_badge_only_when_reviewed(self):
        from reviews.models import Review
        Review.objects.create(tenant=self.tenant, property=self.reviewed, rating=5)
        Review.objects.create(tenant=self.other_tenant, property=self.reviewed, rating=3)

        response = self.client.get('/properties/')
        self.assertContains(response, 'Reviewed Flat')
        self.assertContains(response, 'property-card__rating')
        self.assertContains(response, '4.0')  # (5+3)/2

        properties_by_title = {p['title']: p for p in response.context['properties']}
        self.assertEqual(properties_by_title['Reviewed Flat']['review_count'], 2)
        self.assertEqual(properties_by_title['Unreviewed Flat']['review_count'], 0)
        self.assertIsNone(properties_by_title['Unreviewed Flat']['rating'])

    def test_home_page_featured_grid_shows_real_rating(self):
        from reviews.models import Review
        Review.objects.create(tenant=self.tenant, property=self.reviewed, rating=4)
        response = self.client.get('/')
        self.assertContains(response, 'property-card__rating')
        self.assertContains(response, '4.0')

    def test_no_fake_rating_shown_for_an_unreviewed_listing(self):
        response = self.client.get('/properties/')
        # Only one card has the rating markup (Reviewed Flat has 0 reviews
        # too here), so it should not appear at all on this page.
        self.assertNotContains(response, 'property-card__rating')
