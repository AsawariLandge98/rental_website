from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from properties.models import Property
from .models import Inquiry, InquiryReply


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
        self.assertTrue(
            self.owner.notifications.filter(category='inquiry', message__icontains=self.tenant.full_name).exists(),
        )

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


class InquiryReplyTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner2@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER, mobile_number='9876543210',
        )
        self.tenant = User.objects.create_user(
            email='tenant2@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.property = Property.objects.create(
            owner=self.owner, title='2BHK Flat', status=Property.Status.PUBLISHED,
            city='Nagpur', monthly_rent=15000,
        )
        self.inquiry = Inquiry.objects.create(
            tenant=self.tenant, property=self.property, message='Is this available?',
        )

    def test_tenant_can_view_own_inquiry_detail(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('inquiries:inquiry_detail', args=[self.inquiry.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Is this available?')

    def test_tenant_cannot_view_another_tenants_inquiry_detail(self):
        other_tenant = User.objects.create_user(
            email='other2@example.com', password='StrongPass123',
            full_name='Other Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(other_tenant)
        response = self.client.get(reverse('inquiries:inquiry_detail', args=[self.inquiry.pk]))
        self.assertEqual(response.status_code, 404)

    def test_tenant_reply_creates_message_and_notifies_owner(self):
        self.client.force_login(self.tenant)
        response = self.client.post(
            reverse('inquiries:inquiry_detail', args=[self.inquiry.pk]), {'message': 'Following up!'},
        )
        self.assertRedirects(response, reverse('inquiries:inquiry_detail', args=[self.inquiry.pk]))
        reply = InquiryReply.objects.get(inquiry=self.inquiry, sender=self.tenant)
        self.assertEqual(reply.message, 'Following up!')
        self.assertTrue(
            self.owner.notifications.filter(category='inquiry', message__icontains=self.tenant.full_name).exists(),
        )

    def test_blank_reply_is_not_saved(self):
        self.client.force_login(self.tenant)
        self.client.post(reverse('inquiries:inquiry_detail', args=[self.inquiry.pk]), {'message': '   '})
        self.assertFalse(InquiryReply.objects.filter(inquiry=self.inquiry).exists())

    def test_owner_can_view_and_reply_to_inquiry(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:owner_inquiry_detail', args=[self.inquiry.pk]))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse('dashboard:owner_inquiry_detail', args=[self.inquiry.pk]), {'message': 'Yes, still available!'},
        )
        self.assertRedirects(response, reverse('dashboard:owner_inquiry_detail', args=[self.inquiry.pk]))
        reply = InquiryReply.objects.get(inquiry=self.inquiry, sender=self.owner)
        self.assertEqual(reply.message, 'Yes, still available!')
        self.assertTrue(
            self.tenant.notifications.filter(category='inquiry', message__icontains=self.owner.full_name).exists(),
        )

    def test_owner_cannot_view_another_owners_inquiry(self):
        other_owner = User.objects.create_user(
            email='otherowner2@example.com', password='StrongPass123',
            full_name='Other Owner', role=User.Role.OWNER, mobile_number='9876543211',
        )
        self.client.force_login(other_owner)
        response = self.client.get(reverse('dashboard:owner_inquiry_detail', args=[self.inquiry.pk]))
        self.assertEqual(response.status_code, 404)
