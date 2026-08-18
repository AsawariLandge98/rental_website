from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from properties.models import Property
from .models import Visit


class VisitTests(TestCase):
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
        self.client.force_login(self.tenant)

    def test_schedule_future_visit_succeeds(self):
        future = (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('properties:schedule_visit', args=[self.property.pk]), {'scheduled_at': future})
        self.assertRedirects(response, reverse('properties:detail', args=[self.property.pk]))
        visit = Visit.objects.get(tenant=self.tenant, property=self.property)
        self.assertEqual(visit.status, Visit.Status.SCHEDULED)

    def test_schedule_past_visit_rejected(self):
        past = (timezone.now() - timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M')
        response = self.client.post(reverse('properties:schedule_visit', args=[self.property.pk]), {'scheduled_at': past})
        self.assertRedirects(response, reverse('properties:detail', args=[self.property.pk]))
        self.assertFalse(Visit.objects.filter(tenant=self.tenant, property=self.property).exists())

    def test_cancel_visit(self):
        visit = Visit.objects.create(tenant=self.tenant, property=self.property, scheduled_at=timezone.now() + timezone.timedelta(days=1))
        response = self.client.post(reverse('visits:cancel_visit', args=[visit.pk]))
        self.assertRedirects(response, reverse('visits:my_visits'))
        visit.refresh_from_db()
        self.assertEqual(visit.status, Visit.Status.CANCELLED)
