from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from properties.models import Property
from .models import ContactMessage, NewsletterSubscriber


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
