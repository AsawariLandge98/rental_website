from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from properties.models import Property


class HotelNightlyRateTests(TestCase):
    """Hotel/Guest House/Homestay listings are priced per night — confirms
    the real nightly_rate field (collected by the owner wizard) actually
    renders and filters correctly, instead of every card/detail page
    silently showing monthly_rent labeled "/month"."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.HOTEL,
        )

    def test_hotel_card_shows_nightly_rate_not_monthly_rent(self):
        Property.objects.create(
            owner=self.owner, category=Property.Category.HOTEL, status=Property.Status.PUBLISHED,
            title='Lakeview Stay', city='Manali', monthly_rent=50000, nightly_rate=1500,
        )
        response = self.client.get(reverse('hotels:list'))
        self.assertContains(response, '1,500')
        self.assertContains(response, '/night')
        self.assertNotContains(response, '50,000')

    def test_residential_property_still_shows_monthly_rent(self):
        Property.objects.create(
            owner=self.owner, category=Property.Category.RESIDENTIAL, status=Property.Status.PUBLISHED,
            title='2BHK Flat', city='Pune', monthly_rent=20000,
        )
        response = self.client.get(reverse('properties:search'))
        self.assertContains(response, '20,000')
        self.assertContains(response, '/month')

    def test_budget_filter_matches_nightly_rate_not_monthly_rent(self):
        cheap = Property.objects.create(
            owner=self.owner, category=Property.Category.HOTEL, status=Property.Status.PUBLISHED,
            title='Budget Stay', city='Goa', monthly_rent=90000, nightly_rate=2000,
        )
        expensive = Property.objects.create(
            owner=self.owner, category=Property.Category.HOTEL, status=Property.Status.PUBLISHED,
            title='Luxury Stay', city='Goa', monthly_rent=30000, nightly_rate=8000,
        )
        response = self.client.get(reverse('hotels:list'), {'budget': '0-3000'})
        self.assertContains(response, 'Budget Stay')
        self.assertNotContains(response, 'Luxury Stay')


class HotelRatingBadgeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Tenant', role=User.Role.TENANT,
        )
        self.hotel = Property.objects.create(
            owner=self.owner, category=Property.Category.HOTEL, status=Property.Status.PUBLISHED,
            title='Reviewed Stay', city='Goa', nightly_rate=3000,
        )

    def test_hotels_list_shows_a_real_rating_badge(self):
        from reviews.models import Review
        Review.objects.create(tenant=self.tenant, property=self.hotel, rating=5)
        response = self.client.get(reverse('hotels:list'))
        self.assertContains(response, 'property-card__rating')
        self.assertContains(response, '5.0')
