from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import RoommatePosting


class RoommateListTests(TestCase):
    def setUp(self):
        self.poster = User.objects.create_user(
            email='poster@example.com', password='StrongPass123', full_name='Test Poster', role=User.Role.TENANT,
        )

    def test_no_more_coming_soon_placeholder(self):
        response = self.client.get(reverse('roommates:list'))
        self.assertNotContains(response, 'Profile Coming Soon')

    def test_shows_real_posting(self):
        RoommatePosting.objects.create(
            poster=self.poster, posting_type=RoommatePosting.PostingType.OFFERING,
            room_type='2 BHK Apartment', city='Bengaluru', area_locality='Koramangala', monthly_rent=8000,
        )
        response = self.client.get(reverse('roommates:list'))
        self.assertContains(response, '2 BHK Apartment')
        self.assertContains(response, 'Test Poster')

    def test_inactive_posting_is_hidden(self):
        RoommatePosting.objects.create(
            poster=self.poster, room_type='Hidden Room', city='Pune', monthly_rent=5000, is_active=False,
        )
        response = self.client.get(reverse('roommates:list'))
        self.assertNotContains(response, 'Hidden Room')

    def test_filter_by_posting_type(self):
        RoommatePosting.objects.create(
            poster=self.poster, posting_type=RoommatePosting.PostingType.LOOKING,
            room_type='Looking Post', city='Pune', monthly_rent=5000,
        )
        RoommatePosting.objects.create(
            poster=self.poster, posting_type=RoommatePosting.PostingType.OFFERING,
            room_type='Offering Post', city='Pune', monthly_rent=5000,
        )
        response = self.client.get(reverse('roommates:list'), {'type': 'looking'})
        self.assertContains(response, 'Looking Post')
        self.assertNotContains(response, 'Offering Post')

    def test_filter_by_budget(self):
        RoommatePosting.objects.create(poster=self.poster, room_type='Cheap Room', city='Pune', monthly_rent=5000)
        RoommatePosting.objects.create(poster=self.poster, room_type='Costly Room', city='Pune', monthly_rent=15000)
        response = self.client.get(reverse('roommates:list'), {'budget': '0-7000'})
        self.assertContains(response, 'Cheap Room')
        self.assertNotContains(response, 'Costly Room')

    def test_filter_by_location_search(self):
        RoommatePosting.objects.create(poster=self.poster, room_type='Koramangala Room', city='Bengaluru', area_locality='Koramangala', monthly_rent=8000)
        RoommatePosting.objects.create(poster=self.poster, room_type='Whitefield Room', city='Bengaluru', area_locality='Whitefield', monthly_rent=8000)
        response = self.client.get(reverse('roommates:list'), {'q': 'Koramangala'})
        self.assertContains(response, 'Koramangala Room')
        self.assertNotContains(response, 'Whitefield Room')


class RoommateDetailTests(TestCase):
    def setUp(self):
        self.poster = User.objects.create_user(
            email='poster@example.com', password='StrongPass123', full_name='Test Poster', role=User.Role.TENANT,
            mobile_number='9876543210',
        )
        self.other_user = User.objects.create_user(
            email='other@example.com', password='StrongPass123', full_name='Other User', role=User.Role.TENANT,
        )
        self.posting = RoommatePosting.objects.create(
            poster=self.poster, room_type='2 BHK Apartment', city='Bengaluru', monthly_rent=8000,
            description='Real description here.',
        )

    def test_detail_page_renders_real_content(self):
        response = self.client.get(reverse('roommates:detail', args=[self.posting.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2 BHK Apartment')
        self.assertContains(response, 'Real description here.')

    def test_contact_options_include_call_whatsapp_email(self):
        response = self.client.get(reverse('roommates:detail', args=[self.posting.pk]))
        types = [o['type'] for o in response.context['contact_options']]
        self.assertEqual(set(types), {'call', 'whatsapp', 'email'})

    def test_inactive_posting_404s(self):
        self.posting.is_active = False
        self.posting.save()
        response = self.client.get(reverse('roommates:detail', args=[self.posting.pk]))
        self.assertEqual(response.status_code, 404)

    def test_is_owner_flag(self):
        self.client.force_login(self.poster)
        response = self.client.get(reverse('roommates:detail', args=[self.posting.pk]))
        self.assertTrue(response.context['is_owner'])

        self.client.force_login(self.other_user)
        response = self.client.get(reverse('roommates:detail', args=[self.posting.pk]))
        self.assertFalse(response.context['is_owner'])

    def test_poster_age_uses_real_dob_when_set(self):
        self.poster.date_of_birth = date(2000, 1, 1)
        self.poster.save()
        self.assertIsNotNone(self.posting.poster_age)

    def test_poster_age_is_none_without_dob(self):
        self.assertIsNone(self.posting.poster_age)


class RoommateCreateEditDeleteTests(TestCase):
    def setUp(self):
        self.poster = User.objects.create_user(
            email='poster@example.com', password='StrongPass123', full_name='Test Poster', role=User.Role.TENANT,
        )
        self.other_user = User.objects.create_user(
            email='other@example.com', password='StrongPass123', full_name='Other User', role=User.Role.TENANT,
        )

    def test_anonymous_cannot_create(self):
        response = self.client.get(reverse('roommates:create'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('roommates:create')}")

    def test_create_posting(self):
        self.client.force_login(self.poster)
        response = self.client.post(reverse('roommates:create'), {
            'posting_type': RoommatePosting.PostingType.OFFERING, 'room_type': '3 BHK Flat',
            'city': 'Mumbai', 'area_locality': 'Andheri', 'monthly_rent': 12000,
            'gender_preference': RoommatePosting.Gender.ANY, 'occupation': RoommatePosting.Occupation.ANY,
            'roommates_needed': 1, 'description': '',
        })
        posting = RoommatePosting.objects.get(room_type='3 BHK Flat')
        self.assertRedirects(response, reverse('roommates:detail', args=[posting.pk]))
        self.assertEqual(posting.poster, self.poster)

    def test_cannot_edit_someone_elses_posting(self):
        posting = RoommatePosting.objects.create(poster=self.poster, room_type='My Room', city='Pune', monthly_rent=5000)
        self.client.force_login(self.other_user)
        response = self.client.get(reverse('roommates:edit', args=[posting.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_edit(self):
        posting = RoommatePosting.objects.create(poster=self.poster, room_type='My Room', city='Pune', monthly_rent=5000)
        self.client.force_login(self.poster)
        response = self.client.post(reverse('roommates:edit', args=[posting.pk]), {
            'posting_type': RoommatePosting.PostingType.OFFERING, 'room_type': 'Updated Room',
            'city': 'Pune', 'area_locality': '', 'monthly_rent': 6000,
            'gender_preference': RoommatePosting.Gender.ANY, 'occupation': RoommatePosting.Occupation.ANY,
            'roommates_needed': 1, 'description': '',
        })
        self.assertRedirects(response, reverse('roommates:detail', args=[posting.pk]))
        posting.refresh_from_db()
        self.assertEqual(posting.room_type, 'Updated Room')

    def test_toggle_active(self):
        posting = RoommatePosting.objects.create(poster=self.poster, room_type='My Room', city='Pune', monthly_rent=5000)
        self.client.force_login(self.poster)
        self.client.post(reverse('roommates:toggle_active', args=[posting.pk]))
        posting.refresh_from_db()
        self.assertFalse(posting.is_active)

    def test_cannot_delete_someone_elses_posting(self):
        posting = RoommatePosting.objects.create(poster=self.poster, room_type='My Room', city='Pune', monthly_rent=5000)
        self.client.force_login(self.other_user)
        response = self.client.post(reverse('roommates:delete', args=[posting.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(RoommatePosting.objects.filter(pk=posting.pk).exists())

    def test_owner_can_delete(self):
        posting = RoommatePosting.objects.create(poster=self.poster, room_type='My Room', city='Pune', monthly_rent=5000)
        self.client.force_login(self.poster)
        response = self.client.post(reverse('roommates:delete', args=[posting.pk]))
        self.assertRedirects(response, reverse('roommates:list'))
        self.assertFalse(RoommatePosting.objects.filter(pk=posting.pk).exists())
