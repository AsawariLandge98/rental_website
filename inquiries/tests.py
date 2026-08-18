from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from properties.models import Property
from .models import Inquiry


class InquiryTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER, mobile_number='9876543210',
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.property = Property.objects.create(
            owner=self.owner, title='2BHK Flat', status=Property.Status.PUBLISHED,
            city='Nagpur', monthly_rent=15000,
        )

    def test_tenant_can_send_inquiry(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('properties:send_inquiry', args=[self.property.pk]), {'message': 'Hi'})
        self.assertRedirects(response, reverse('properties:detail', args=[self.property.pk]))
        inquiry = Inquiry.objects.get(tenant=self.tenant, property=self.property)
        self.assertEqual(inquiry.status, Inquiry.Status.OPEN)
        self.assertTrue(self.tenant.notifications.filter(category='inquiry').exists())

    def test_owner_cannot_send_inquiry(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('properties:send_inquiry', args=[self.property.pk]), {'message': 'Hi'})
        self.assertEqual(response.status_code, 403)

    def test_tenant_can_close_own_inquiry(self):
        self.client.force_login(self.tenant)
        inquiry = Inquiry.objects.create(tenant=self.tenant, property=self.property)
        response = self.client.post(reverse('inquiries:close_inquiry', args=[inquiry.pk]))
        self.assertRedirects(response, reverse('inquiries:my_inquiries'))
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, Inquiry.Status.CLOSED)

    def test_tenant_cannot_close_another_tenants_inquiry(self):
        other_tenant = User.objects.create_user(
            email='other@example.com', password='StrongPass123',
            full_name='Other Tenant', role=User.Role.TENANT,
        )
        inquiry = Inquiry.objects.create(tenant=other_tenant, property=self.property)
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('inquiries:close_inquiry', args=[inquiry.pk]))
        self.assertEqual(response.status_code, 404)
