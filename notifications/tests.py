from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import Notification, notify


class NotificationTests(TestCase):
    def setUp(self):
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(self.tenant)

    def test_notify_helper_creates_notification(self):
        n = notify(self.tenant, 'Hello', category=Notification.Category.SYSTEM)
        self.assertFalse(n.is_read)
        self.assertEqual(self.tenant.notifications.count(), 1)

    def test_mark_read(self):
        n = notify(self.tenant, 'Hello')
        response = self.client.get(reverse('notifications:mark_read', args=[n.pk]))
        self.assertEqual(response.status_code, 302)
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_cannot_mark_another_users_notification_read(self):
        other = User.objects.create_user(
            email='other@example.com', password='StrongPass123',
            full_name='Other', role=User.Role.TENANT,
        )
        n = notify(other, 'Hello')
        response = self.client.get(reverse('notifications:mark_read', args=[n.pk]))
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read(self):
        notify(self.tenant, 'One')
        notify(self.tenant, 'Two')
        response = self.client.post(reverse('notifications:mark_all_read'))
        self.assertRedirects(response, reverse('notifications:list'))
        self.assertEqual(self.tenant.notifications.filter(is_read=False).count(), 0)
