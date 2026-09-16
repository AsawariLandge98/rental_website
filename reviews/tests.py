from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification
from properties.models import Property
from visits.models import Visit
from .models import Review


class SubmitReviewTests(TestCase):
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
        self.client.force_login(self.tenant)

    def test_cannot_review_without_a_completed_visit(self):
        response = self.client.post(reverse('reviews:submit', args=[self.property.pk]), {
            'rating': 5, 'comment': 'Great place!',
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.property.pk]))
        self.assertFalse(Review.objects.filter(tenant=self.tenant, property=self.property).exists())

    def test_can_review_after_a_completed_visit(self):
        Visit.objects.create(
            tenant=self.tenant, property=self.property,
            scheduled_at=timezone.now() - timezone.timedelta(days=1), status=Visit.Status.COMPLETED,
        )
        response = self.client.post(reverse('reviews:submit', args=[self.property.pk]), {
            'rating': 5, 'comment': 'Great place, real experience.',
        })
        self.assertRedirects(response, reverse('properties:detail', args=[self.property.pk]))
        review = Review.objects.get(tenant=self.tenant, property=self.property)
        self.assertEqual(review.rating, 5)
        self.assertTrue(
            Notification.objects.filter(user=self.owner, message__icontains='5-star review').exists(),
        )

    def test_cannot_review_with_only_a_scheduled_pending_visit(self):
        Visit.objects.create(
            tenant=self.tenant, property=self.property,
            scheduled_at=timezone.now() + timezone.timedelta(days=1), status=Visit.Status.SCHEDULED,
        )
        response = self.client.post(reverse('reviews:submit', args=[self.property.pk]), {
            'rating': 4, 'comment': 'Looking forward to it.',
        })
        self.assertFalse(Review.objects.filter(tenant=self.tenant, property=self.property).exists())

    def test_resubmitting_updates_the_existing_review_not_a_duplicate(self):
        Visit.objects.create(
            tenant=self.tenant, property=self.property,
            scheduled_at=timezone.now() - timezone.timedelta(days=1), status=Visit.Status.COMPLETED,
        )
        self.client.post(reverse('reviews:submit', args=[self.property.pk]), {'rating': 3, 'comment': 'Okay.'})
        self.client.post(reverse('reviews:submit', args=[self.property.pk]), {'rating': 5, 'comment': 'Actually great!'})
        self.assertEqual(Review.objects.filter(tenant=self.tenant, property=self.property).count(), 1)
        review = Review.objects.get(tenant=self.tenant, property=self.property)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Actually great!')

    def test_one_review_per_tenant_per_property_db_constraint(self):
        Review.objects.create(tenant=self.tenant, property=self.property, rating=4)
        with self.assertRaises(Exception):
            Review.objects.create(tenant=self.tenant, property=self.property, rating=2)

    def test_invalid_rating_rejected(self):
        Visit.objects.create(
            tenant=self.tenant, property=self.property,
            scheduled_at=timezone.now() - timezone.timedelta(days=1), status=Visit.Status.COMPLETED,
        )
        response = self.client.post(reverse('reviews:submit', args=[self.property.pk]), {'rating': 9, 'comment': ''})
        self.assertFalse(Review.objects.filter(tenant=self.tenant, property=self.property).exists())

    def test_owner_cannot_submit_a_review(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('reviews:submit', args=[self.property.pk]), {'rating': 5, 'comment': ''})
        self.assertEqual(response.status_code, 403)
