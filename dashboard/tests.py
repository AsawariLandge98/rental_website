from datetime import date, timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import OwnerProfile, TenantProfile, User
from bookings.models import Booking
from cms.models import ContentBlock, FAQ, LegalPage, PageSEO, SiteSettings
from inquiries.models import Inquiry
from notifications.models import Notification
from properties.models import Property
from reviews.models import Review
from subscriptions.models import Payment, SubscriptionPlan
from visits.models import Visit
from .models import AuditLog, SupportTicket


class TenantDashboardAccessTests(TestCase):
    def setUp(self):
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )

    def test_tenant_can_reach_dashboard_home(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:tenant'))
        self.assertEqual(response.status_code, 200)

    def test_owner_is_blocked_from_tenant_dashboard(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:tenant'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse('dashboard:tenant'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('dashboard:tenant')}")

    def test_visiting_home_creates_tenant_profile(self):
        self.client.force_login(self.tenant)
        self.assertFalse(TenantProfile.objects.filter(user=self.tenant).exists())
        self.client.get(reverse('dashboard:tenant'))
        self.assertTrue(TenantProfile.objects.filter(user=self.tenant).exists())


class ProfileAndSettingsTests(TestCase):
    def setUp(self):
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(self.tenant)

    def test_profile_update(self):
        response = self.client.post(reverse('dashboard:tenant_profile'), {
            'full_name': 'Updated Name',
            'mobile_number': '9876543210',
            'occupation': 'Engineer',
            'preferred_city': 'Nagpur',
        })
        self.assertRedirects(response, reverse('dashboard:tenant_profile'))
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.full_name, 'Updated Name')
        self.assertEqual(self.tenant.tenant_profile.occupation, 'Engineer')

    def test_notification_preferences_update(self):
        response = self.client.post(reverse('dashboard:tenant_settings_notifications'), {
            'email_notifications': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:tenant_settings'))
        profile = TenantProfile.objects.get(user=self.tenant)
        self.assertTrue(profile.email_notifications)
        self.assertFalse(profile.sms_notifications)

    def test_password_change(self):
        response = self.client.post(reverse('dashboard:tenant_settings_password'), {
            'old_password': 'StrongPass123',
            'new_password1': 'NewStrongPass456',
            'new_password2': 'NewStrongPass456',
        })
        self.assertRedirects(response, reverse('dashboard:tenant_settings'))
        self.client.logout()
        self.assertTrue(self.client.login(email='tenant@example.com', password='NewStrongPass456'))

    def test_delete_account_requires_confirmation_text(self):
        response = self.client.post(reverse('dashboard:tenant_settings_delete'), {'confirm': 'nope'})
        self.assertRedirects(response, reverse('dashboard:tenant_settings'))
        self.tenant.refresh_from_db()
        self.assertTrue(self.tenant.is_active)

    def test_delete_account_deactivates_and_logs_out(self):
        response = self.client.post(reverse('dashboard:tenant_settings_delete'), {'confirm': 'DELETE'})
        self.assertRedirects(response, reverse('accounts:login'))
        self.tenant.refresh_from_db()
        self.assertFalse(self.tenant.is_active)

    def test_support_ticket_submission(self):
        response = self.client.post(reverse('dashboard:tenant_help'), {
            'subject': 'Cannot upload photo',
            'category': SupportTicket.Category.PROPERTY,
            'description': 'The upload button does nothing.',
        })
        self.assertRedirects(response, reverse('dashboard:tenant_help'))
        self.assertTrue(SupportTicket.objects.filter(user=self.tenant, subject='Cannot upload photo').exists())


class OwnerDashboardAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.hotel_owner = User.objects.create_user(
            email='hotel@example.com', password='StrongPass123',
            full_name='Test Hotel Owner', role=User.Role.HOTEL,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def test_owner_can_reach_dashboard_home(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('dashboard:owner'))
        self.assertEqual(response.status_code, 200)

    def test_hotel_owner_can_reach_dashboard_home(self):
        self.client.force_login(self.hotel_owner)
        response = self.client.get(reverse('dashboard:hotel'))
        self.assertEqual(response.status_code, 200)

    def test_tenant_is_blocked_from_owner_dashboard(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:owner'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse('dashboard:owner'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('dashboard:owner')}")

    def test_owner_routes_reachable_for_owner_and_blocked_for_tenant(self):
        self.client.force_login(self.owner)
        for name in ('owner_inquiries', 'owner_visits', 'owner_settings', 'owner_help'):
            response = self.client.get(reverse(f'dashboard:{name}'))
            self.assertEqual(response.status_code, 200, f'{name} should be reachable by an owner')

        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:owner_inquiries'))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_submit_a_real_support_ticket(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('dashboard:owner_help'), {
            'subject': 'Payout not received',
            'category': SupportTicket.Category.PAYMENT,
            'description': 'My last payout is missing.',
        })
        self.assertRedirects(response, reverse('dashboard:owner_help'))
        self.assertTrue(SupportTicket.objects.filter(user=self.owner, subject='Payout not received').exists())


class OwnerSettingsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.client.force_login(self.owner)

    def test_notification_preferences_update(self):
        response = self.client.post(reverse('dashboard:owner_settings_notifications'), {
            'email_notifications': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:owner_settings'))
        profile = OwnerProfile.objects.get(user=self.owner)
        self.assertTrue(profile.email_notifications)
        self.assertFalse(profile.sms_notifications)

    def test_privacy_preferences_update(self):
        response = self.client.post(reverse('dashboard:owner_settings_privacy'), {
            'allow_tenant_contact': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:owner_settings'))
        profile = OwnerProfile.objects.get(user=self.owner)
        self.assertTrue(profile.allow_tenant_contact)
        self.assertFalse(profile.show_contact_to_tenants)

    def test_password_change(self):
        response = self.client.post(reverse('dashboard:owner_settings_password'), {
            'old_password': 'StrongPass123',
            'new_password1': 'NewStrongPass456',
            'new_password2': 'NewStrongPass456',
        })
        self.assertRedirects(response, reverse('dashboard:owner_settings'))
        self.client.logout()
        self.assertTrue(self.client.login(email='owner@example.com', password='NewStrongPass456'))

    def test_delete_account_requires_confirmation_text(self):
        response = self.client.post(reverse('dashboard:owner_settings_delete'), {'confirm': 'nope'})
        self.assertRedirects(response, reverse('dashboard:owner_settings'))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_delete_account_deactivates_and_logs_out(self):
        response = self.client.post(reverse('dashboard:owner_settings_delete'), {'confirm': 'DELETE'})
        self.assertRedirects(response, reverse('accounts:login'))
        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_active)

    def test_tenant_is_blocked_from_owner_settings(self):
        tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(tenant)
        response = self.client.get(reverse('dashboard:owner_settings'))
        self.assertEqual(response.status_code, 403)


class HelpWidgetQuickTicketTests(TestCase):
    """The floating Help & Support widget's compact submit endpoint —
    reachable from any page, for Tenant/Owner/Hotel accounts only."""

    def setUp(self):
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.admin = User.objects.create_user(
            email='admin@example.com', password='StrongPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )

    def test_tenant_quick_ticket_records_page_url_and_redirects_back(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('dashboard:quick_support_ticket'), {
            'subject': 'Question about this listing',
            'category': SupportTicket.Category.PROPERTY,
            'description': 'Is this still available?',
            'page_url': '/properties/42/',
            'next': '/properties/42/',
        })
        self.assertRedirects(response, '/properties/42/', fetch_redirect_response=False)
        ticket = SupportTicket.objects.get(user=self.tenant)
        self.assertEqual(ticket.page_url, '/properties/42/')

    def test_owner_quick_ticket_via_ajax_returns_json(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('dashboard:quick_support_ticket'),
            {'subject': 'Quick query', 'category': SupportTicket.Category.OTHER, 'description': 'Help needed.'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})
        self.assertTrue(SupportTicket.objects.filter(user=self.owner, subject='Quick query').exists())

    def test_admin_cannot_use_quick_ticket_endpoint(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('dashboard:quick_support_ticket'),
            {'subject': 'x', 'category': SupportTicket.Category.OTHER, 'description': 'y'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SupportTicket.objects.filter(user=self.admin).exists())

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.post(reverse('dashboard:quick_support_ticket'), {
            'subject': 'x', 'category': SupportTicket.Category.OTHER, 'description': 'y',
        })
        self.assertRedirects(response, f"/accounts/login/?next={reverse('dashboard:quick_support_ticket')}")


class OwnerDashboardStatsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.other_owner = User.objects.create_user(
            email='other-owner@example.com', password='StrongPass123',
            full_name='Other Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.published = Property.objects.create(
            owner=self.owner, title='Published Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        Property.objects.create(owner=self.owner, title='Draft Flat', status=Property.Status.DRAFT)
        Property.objects.create(owner=self.other_owner, title='Not mine', status=Property.Status.PUBLISHED)

        Inquiry.objects.create(tenant=self.tenant, property=self.published, message='Interested')
        Visit.objects.create(
            tenant=self.tenant, property=self.published,
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
        )

        self.client.force_login(self.owner)

    def test_dashboard_stats_reflect_only_this_owners_data(self):
        response = self.client.get(reverse('dashboard:owner'))
        stats = response.context['stats']
        self.assertEqual(stats['total_listings'], 2)
        self.assertEqual(stats['active_listings'], 1)
        self.assertEqual(stats['draft_listings'], 1)
        self.assertEqual(stats['new_inquiries'], 1)
        self.assertEqual(stats['scheduled_visits'], 1)

    def test_recent_inquiries_and_visits_show_up(self):
        response = self.client.get(reverse('dashboard:owner'))
        self.assertEqual(list(response.context['recent_inquiries']), [Inquiry.objects.get()])
        self.assertEqual(list(response.context['upcoming_visits']), [Visit.objects.get()])


class MyPropertiesTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.other_owner = User.objects.create_user(
            email='other-owner@example.com', password='StrongPass123',
            full_name='Other Owner', role=User.Role.OWNER,
        )
        self.mine = Property.objects.create(
            owner=self.owner, title='Sunshine Apartment', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        Property.objects.create(owner=self.owner, title='Draft Home', status=Property.Status.DRAFT)
        Property.objects.create(owner=self.other_owner, title='Someone Else Flat', status=Property.Status.PUBLISHED)
        self.client.force_login(self.owner)

    def test_only_shows_own_properties(self):
        response = self.client.get(reverse('properties:my_listings'))
        titles = {p.title for p in response.context['properties']}
        self.assertEqual(titles, {'Sunshine Apartment', 'Draft Home'})

    def test_search_filters_by_title(self):
        response = self.client.get(reverse('properties:my_listings'), {'q': 'Sunshine'})
        titles = [p.title for p in response.context['properties']]
        self.assertEqual(titles, ['Sunshine Apartment'])

    def test_status_filter(self):
        response = self.client.get(reverse('properties:my_listings'), {'status': 'draft'})
        titles = [p.title for p in response.context['properties']]
        self.assertEqual(titles, ['Draft Home'])

    def test_stats_are_not_affected_by_filters(self):
        response = self.client.get(reverse('properties:my_listings'), {'q': 'Sunshine'})
        self.assertEqual(response.context['stats']['total'], 2)

    def test_inquiries_count_annotated_per_property(self):
        Inquiry.objects.create(
            tenant=User.objects.create_user(email='t1@example.com', password='StrongPass123', role=User.Role.TENANT),
            property=self.mine, message='Hi',
        )
        response = self.client.get(reverse('properties:my_listings'))
        by_title = {p.title: p.inquiries_count for p in response.context['properties']}
        self.assertEqual(by_title['Sunshine Apartment'], 1)
        self.assertEqual(by_title['Draft Home'], 0)


class OwnerProfileTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.client.force_login(self.owner)

    def test_profile_update(self):
        response = self.client.post(reverse('dashboard:owner_profile'), {
            'full_name': 'Updated Owner Name',
            'mobile_number': '9876543210',
        })
        self.assertRedirects(response, reverse('dashboard:owner_profile'))
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.full_name, 'Updated Owner Name')

    def test_password_change(self):
        response = self.client.post(reverse('dashboard:owner_profile_password'), {
            'old_password': 'StrongPass123',
            'new_password1': 'NewStrongPass456',
            'new_password2': 'NewStrongPass456',
        })
        self.assertRedirects(response, reverse('dashboard:owner_profile'))
        self.client.logout()
        self.assertTrue(self.client.login(email='owner@example.com', password='NewStrongPass456'))


class AdminDashboardAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.super_admin = User.objects.create_user(
            email='super-admin@example.com', password='AdminPass123',
            full_name='Test Super Admin', role=User.Role.SUPER_ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def test_admin_can_reach_dashboard_home(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('dashboard:admin'))
        self.assertEqual(response.status_code, 200)

    def test_super_admin_can_reach_dashboard_home(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('dashboard:super_admin'))
        self.assertEqual(response.status_code, 200)

    def test_owner_and_tenant_are_blocked_from_admin_dashboard(self):
        for user in (self.owner, self.tenant):
            self.client.force_login(user)
            response = self.client.get(reverse('dashboard:admin'))
            self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse('dashboard:admin'))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('dashboard:admin')}")

    def test_admin_routes_reachable_for_admin_and_blocked_for_tenant(self):
        self.client.force_login(self.admin)
        for name in (
            'admin_properties', 'admin_inquiries', 'admin_visits', 'admin_payments',
            'admin_subscriptions', 'admin_reports', 'admin_support', 'admin_cms',
        ):
            response = self.client.get(reverse(f'dashboard:{name}'))
            self.assertEqual(response.status_code, 200, f'{name} should be reachable by an admin')

        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_properties'))
        self.assertEqual(response.status_code, 403)

    def test_settings_and_admin_users_are_super_admin_only(self):
        self.client.force_login(self.super_admin)
        self.assertEqual(self.client.get(reverse('dashboard:admin_settings')).status_code, 200)
        self.assertEqual(self.client.get(reverse('dashboard:admin_internal_users')).status_code, 200)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('dashboard:admin_settings')).status_code, 403)
        self.assertEqual(self.client.get(reverse('dashboard:admin_internal_users')).status_code, 403)

    @override_settings(RAZORPAY_KEY_ID='', RAZORPAY_KEY_SECRET='', GOOGLE_OAUTH_CONFIGURED=False, EMAIL_CONFIGURED=False)
    def test_settings_page_shows_unconfigured_integrations_honestly(self):
        # Forced to a known unconfigured state via override_settings rather
        # than relying on whatever real credentials happen to be in this
        # machine's .env (e.g. a real Gmail SMTP account was added to this
        # project's own .env for actual use — the test shouldn't care).
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('dashboard:admin_settings'))
        names = [i['name'] for i in response.context['integrations']]
        self.assertEqual(names, ['Razorpay Payments', 'Google Sign-In', 'Email (SMTP)'])
        self.assertTrue(all(i['configured'] is False for i in response.context['integrations']))
        self.assertFalse(response.context['email_configured'])
        self.assertIn('Console', response.context['email_mode'])

    @override_settings(RAZORPAY_KEY_ID='rzp_test_x', RAZORPAY_KEY_SECRET='secret', GOOGLE_OAUTH_CONFIGURED=True, EMAIL_CONFIGURED=True, EMAIL_HOST='smtp.example.com')
    def test_settings_page_shows_configured_integrations_honestly(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('dashboard:admin_settings'))
        self.assertTrue(all(i['configured'] is True for i in response.context['integrations']))
        self.assertTrue(response.context['email_configured'])
        self.assertIn('smtp.example.com', response.context['email_mode'])

    def test_send_test_email_without_smtp_configured_shows_real_error(self):
        # No EMAIL_HOST_USER/PASSWORD in the test environment — must not
        # pretend to send, and must not crash.
        self.client.force_login(self.super_admin)
        response = self.client.post(reverse('dashboard:admin_send_test_email'))
        self.assertRedirects(response, reverse('dashboard:admin_settings'))

    def test_send_test_email_is_admin_only_not_regular_admin(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('dashboard:admin_send_test_email'))
        self.assertEqual(response.status_code, 403)

    @override_settings(EMAIL_CONFIGURED=True, EMAIL_HOST='smtp.example.com')
    def test_send_test_email_actually_sends_once_configured(self):
        self.client.force_login(self.super_admin)
        response = self.client.post(reverse('dashboard:admin_send_test_email'))
        self.assertRedirects(response, reverse('dashboard:admin_settings'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.super_admin.email])
        self.assertEqual(mail.outbox[0].subject, 'Rentora — Test Email')

    def test_update_property_photo_limits(self):
        self.client.force_login(self.super_admin)
        response = self.client.post(reverse('dashboard:admin_settings'), {
            'min_photos_to_publish': 3, 'max_photos_per_listing': 30,
        })
        self.assertRedirects(response, reverse('dashboard:admin_settings'))
        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.min_photos_to_publish, 3)
        self.assertEqual(settings_obj.max_photos_per_listing, 30)

    def test_photo_limit_update_is_logged(self):
        self.client.force_login(self.super_admin)
        self.client.post(reverse('dashboard:admin_settings'), {
            'min_photos_to_publish': 3, 'max_photos_per_listing': 30,
        })
        self.assertTrue(AuditLog.objects.filter(target_type='SiteSettings', target_id=1).exists())


class AdminDashboardStatsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        User.objects.create_user(
            email='blocked-tenant@example.com', password='StrongPass123',
            full_name='Blocked Tenant', role=User.Role.TENANT, is_active=False,
        )
        self.published = Property.objects.create(
            owner=self.owner, title='Published Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        Inquiry.objects.create(tenant=self.tenant, property=self.published, message='Interested')
        Visit.objects.create(
            tenant=self.tenant, property=self.published,
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
        )
        SupportTicket.objects.create(
            user=self.tenant, subject='Help', category=SupportTicket.Category.OTHER, description='...',
        )
        self.client.force_login(self.admin)

    def test_dashboard_stats_are_platform_wide(self):
        response = self.client.get(reverse('dashboard:admin'))
        stats = response.context['stats']
        self.assertEqual(stats['total_users'], 3)  # owner + tenant + blocked tenant, not the admin itself
        self.assertEqual(stats['blocked_users'], 1)
        self.assertEqual(stats['active_users'], 2)
        self.assertEqual(stats['total_properties'], 1)
        self.assertEqual(stats['active_properties'], 1)
        self.assertEqual(stats['total_inquiries'], 1)
        self.assertEqual(stats['scheduled_visits'], 1)
        self.assertEqual(stats['open_tickets'], 1)

    def test_recent_activity_includes_multiple_kinds(self):
        response = self.client.get(reverse('dashboard:admin'))
        kinds = {item['icon'] for item in response.context['recent_activity']}
        self.assertTrue({'user', 'building', 'chat', 'headset'}.issubset(kinds))


class AdminUsersTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.other_admin = User.objects.create_user(
            email='other-admin@example.com', password='AdminPass123',
            full_name='Other Admin', role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Rajesh Kumar', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Anjali Sharma', role=User.Role.TENANT,
        )
        self.client.force_login(self.admin)

    def test_admin_accounts_are_never_listed(self):
        response = self.client.get(reverse('dashboard:admin_users'))
        listed_emails = {u.email for u in response.context['users_page']}
        self.assertNotIn(self.admin.email, listed_emails)
        self.assertNotIn(self.other_admin.email, listed_emails)
        self.assertIn(self.owner.email, listed_emails)
        self.assertIn(self.tenant.email, listed_emails)

    def test_search_filters_by_name(self):
        response = self.client.get(reverse('dashboard:admin_users'), {'q': 'Rajesh'})
        emails = [u.email for u in response.context['users_page']]
        self.assertEqual(emails, [self.owner.email])

    def test_role_filter(self):
        response = self.client.get(reverse('dashboard:admin_users'), {'role': 'tenant'})
        emails = [u.email for u in response.context['users_page']]
        self.assertEqual(emails, [self.tenant.email])

    def test_block_sets_inactive_and_prevents_login(self):
        response = self.client.post(reverse('dashboard:admin_user_block', args=[self.tenant.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_users'))
        self.tenant.refresh_from_db()
        self.assertFalse(self.tenant.is_active)
        self.assertFalse(self.client.login(email='tenant@example.com', password='StrongPass123'))

    def test_unblock_reverses_block(self):
        self.tenant.is_active = False
        self.tenant.save(update_fields=['is_active'])
        response = self.client.post(reverse('dashboard:admin_user_unblock', args=[self.tenant.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_users'))
        self.tenant.refresh_from_db()
        self.assertTrue(self.tenant.is_active)

    def test_cannot_block_another_admin(self):
        response = self.client.post(reverse('dashboard:admin_user_block', args=[self.other_admin.pk]))
        self.assertEqual(response.status_code, 404)
        self.other_admin.refresh_from_db()
        self.assertTrue(self.other_admin.is_active)


class AdminProfileTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.client.force_login(self.admin)

    def test_profile_update(self):
        response = self.client.post(reverse('dashboard:admin_profile'), {
            'full_name': 'Updated Admin Name',
            'mobile_number': '9876543210',
        })
        self.assertRedirects(response, reverse('dashboard:admin_profile'))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.full_name, 'Updated Admin Name')

    def test_password_change(self):
        response = self.client.post(reverse('dashboard:admin_profile_password'), {
            'old_password': 'AdminPass123',
            'new_password1': 'NewAdminPass456',
            'new_password2': 'NewAdminPass456',
        })
        self.assertRedirects(response, reverse('dashboard:admin_profile'))
        self.client.logout()
        self.assertTrue(self.client.login(email='admin@example.com', password='NewAdminPass456'))


class AdminPropertiesTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.published = Property.objects.create(
            owner=self.owner, title='Sunshine Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        self.draft = Property.objects.create(owner=self.owner, title='Draft Flat', status=Property.Status.DRAFT)
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_properties'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('dashboard:admin_property_detail', args=[self.published.pk]))
        self.assertEqual(response.status_code, 200)

        for user in (self.owner, self.tenant):
            self.client.force_login(user)
            response = self.client.get(reverse('dashboard:admin_properties'))
            self.assertEqual(response.status_code, 403)

    def test_stats(self):
        response = self.client.get(reverse('dashboard:admin_properties'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['active'], 1)
        self.assertEqual(stats['pending_review'], 1)
        self.assertEqual(stats['rejected'], 0)
        self.assertEqual(stats['draft'], 1)

    def test_search_and_status_filters(self):
        response = self.client.get(reverse('dashboard:admin_properties'), {'q': 'Sunshine'})
        titles = [p.title for p in response.context['properties']]
        self.assertEqual(titles, ['Sunshine Flat'])

        response = self.client.get(reverse('dashboard:admin_properties'), {'status': 'draft'})
        titles = [p.title for p in response.context['properties']]
        self.assertEqual(titles, ['Draft Flat'])

    def test_approve_sets_verification_and_notifies_owner(self):
        response = self.client.post(reverse('dashboard:admin_property_approve', args=[self.published.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_property_detail', args=[self.published.pk]))
        self.published.refresh_from_db()
        self.assertIsNotNone(self.published.verified_at)
        self.assertEqual(self.published.verified_by, self.admin)
        self.assertEqual(self.published.verification_state, 'verified')
        self.assertTrue(Notification.objects.filter(user=self.owner, message__icontains='verified').exists())

    def test_reject_requires_a_reason(self):
        response = self.client.post(reverse('dashboard:admin_property_reject', args=[self.published.pk]), {'reason': ''})
        self.assertEqual(response.status_code, 200)
        self.published.refresh_from_db()
        self.assertEqual(self.published.rejection_reason, '')

    def test_reject_with_reason_returns_listing_to_draft_and_notifies_owner(self):
        response = self.client.post(
            reverse('dashboard:admin_property_reject', args=[self.published.pk]),
            {'reason': 'Photos are too blurry to verify the property.'},
        )
        self.assertRedirects(response, reverse('dashboard:admin_properties'))
        self.published.refresh_from_db()
        self.assertEqual(self.published.status, Property.Status.DRAFT)
        self.assertEqual(self.published.rejection_reason, 'Photos are too blurry to verify the property.')
        self.assertIsNone(self.published.verified_at)
        self.assertEqual(self.published.verification_state, 'rejected')
        self.assertTrue(Notification.objects.filter(user=self.owner, message__icontains='rejected').exists())

    def test_admin_can_moderate_any_owners_property_regardless_of_ownership(self):
        response = self.client.post(
            reverse('dashboard:admin_property_set_status', args=[self.published.pk, 'archived']),
        )
        self.assertRedirects(response, reverse('dashboard:admin_properties'))
        self.published.refresh_from_db()
        self.assertEqual(self.published.status, Property.Status.ARCHIVED)
        self.assertTrue(Notification.objects.filter(user=self.owner, message__icontains='archived').exists())


class AdminInquiriesVisitsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.other_tenant = User.objects.create_user(
            email='tenant2@example.com', password='StrongPass123',
            full_name='Other Tenant', role=User.Role.TENANT,
        )
        self.published = Property.objects.create(
            owner=self.owner, title='Sunshine Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        self.open_inquiry = Inquiry.objects.create(tenant=self.tenant, property=self.published, message='Hi')
        self.closed_inquiry = Inquiry.objects.create(
            tenant=self.other_tenant, property=self.published, message='Hi', status=Inquiry.Status.CLOSED,
        )
        self.scheduled_visit = Visit.objects.create(
            tenant=self.tenant, property=self.published,
            scheduled_at=timezone.now() + timezone.timedelta(days=1), status=Visit.Status.SCHEDULED,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_inquiries'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('dashboard:admin_visits'))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_inquiries'))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('dashboard:admin_visits'))
        self.assertEqual(response.status_code, 403)

    def test_inquiries_stats_and_status_filter(self):
        response = self.client.get(reverse('dashboard:admin_inquiries'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['open'], 1)
        self.assertEqual(stats['closed'], 1)

        response = self.client.get(reverse('dashboard:admin_inquiries'), {'status': 'closed'})
        ids = [i.pk for i in response.context['inquiries']]
        self.assertEqual(ids, [self.closed_inquiry.pk])

    def test_close_and_reopen_inquiry(self):
        response = self.client.post(
            reverse('dashboard:admin_inquiry_set_status', args=[self.open_inquiry.pk, 'closed']),
        )
        self.assertRedirects(response, reverse('dashboard:admin_inquiries'))
        self.open_inquiry.refresh_from_db()
        self.assertEqual(self.open_inquiry.status, Inquiry.Status.CLOSED)

        response = self.client.post(
            reverse('dashboard:admin_inquiry_set_status', args=[self.open_inquiry.pk, 'open']),
        )
        self.assertRedirects(response, reverse('dashboard:admin_inquiries'))
        self.open_inquiry.refresh_from_db()
        self.assertEqual(self.open_inquiry.status, Inquiry.Status.OPEN)

    def test_visits_stats(self):
        response = self.client.get(reverse('dashboard:admin_visits'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['pending'], 0)
        self.assertEqual(stats['scheduled'], 1)
        self.assertEqual(stats['completed'], 0)
        self.assertEqual(stats['cancelled'], 0)

    def test_cancel_visit_notifies_tenant(self):
        response = self.client.post(reverse('dashboard:admin_visit_cancel', args=[self.scheduled_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_visits'))
        self.scheduled_visit.refresh_from_db()
        self.assertEqual(self.scheduled_visit.status, Visit.Status.CANCELLED)
        self.assertTrue(Notification.objects.filter(user=self.tenant, message__icontains='cancelled').exists())

    def test_cancel_pending_visit(self):
        pending_visit = Visit.objects.create(
            tenant=self.tenant, property=self.published, scheduled_at=timezone.now() + timezone.timedelta(days=1),
        )
        response = self.client.post(reverse('dashboard:admin_visit_cancel', args=[pending_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_visits'))
        pending_visit.refresh_from_db()
        self.assertEqual(pending_visit.status, Visit.Status.CANCELLED)


class AdminReviewsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.published = Property.objects.create(
            owner=self.owner, title='Sunshine Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        self.review = Review.objects.create(
            tenant=self.tenant, property=self.published, rating=5, comment='Loved it here.',
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_reviews'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_reviews'))
        self.assertEqual(response.status_code, 403)

    def test_stats_and_listing(self):
        response = self.client.get(reverse('dashboard:admin_reviews'))
        self.assertEqual(response.context['stats']['total'], 1)
        self.assertEqual(response.context['stats']['average'], 5)
        ids = {r.pk for r in response.context['reviews']}
        self.assertEqual(ids, {self.review.pk})

    def test_search_by_comment(self):
        response = self.client.get(reverse('dashboard:admin_reviews'), {'q': 'Loved'})
        ids = {r.pk for r in response.context['reviews']}
        self.assertEqual(ids, {self.review.pk})
        response = self.client.get(reverse('dashboard:admin_reviews'), {'q': 'nonexistent-text'})
        self.assertEqual(response.context['reviews'].paginator.count, 0)

    def test_filter_by_rating(self):
        Review.objects.create(
            tenant=User.objects.create_user(
                email='tenant2@example.com', password='StrongPass123', full_name='Tenant Two', role=User.Role.TENANT,
            ),
            property=self.published, rating=2,
        )
        response = self.client.get(reverse('dashboard:admin_reviews'), {'rating': '5'})
        ids = {r.pk for r in response.context['reviews']}
        self.assertEqual(ids, {self.review.pk})

    def test_delete_review_is_logged(self):
        response = self.client.post(reverse('dashboard:admin_review_delete', args=[self.review.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_reviews'))
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())
        self.assertTrue(AuditLog.objects.filter(target_type='Review').exists())

    def test_regular_user_cannot_delete_a_review(self):
        self.client.force_login(self.tenant)
        response = self.client.post(reverse('dashboard:admin_review_delete', args=[self.review.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Review.objects.filter(pk=self.review.pk).exists())


class OwnerInquiriesVisitsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.other_owner = User.objects.create_user(
            email='owner2@example.com', password='StrongPass123',
            full_name='Other Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.other_tenant = User.objects.create_user(
            email='tenant2@example.com', password='StrongPass123',
            full_name='Other Tenant', role=User.Role.TENANT,
        )
        self.published = Property.objects.create(
            owner=self.owner, title='Sunshine Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        self.other_owner_property = Property.objects.create(
            owner=self.other_owner, title='Other Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=12000,
        )
        self.open_inquiry = Inquiry.objects.create(tenant=self.tenant, property=self.published, message='Hi')
        self.closed_inquiry = Inquiry.objects.create(
            tenant=self.other_tenant, property=self.published, message='Hi', status=Inquiry.Status.CLOSED,
        )
        self.other_owner_inquiry = Inquiry.objects.create(
            tenant=self.tenant, property=self.other_owner_property, message='Hi',
        )
        self.scheduled_visit = Visit.objects.create(
            tenant=self.tenant, property=self.published,
            scheduled_at=timezone.now() + timezone.timedelta(days=1), status=Visit.Status.SCHEDULED,
        )
        self.pending_visit = Visit.objects.create(
            tenant=self.other_tenant, property=self.published,
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
        )
        self.other_owner_visit = Visit.objects.create(
            tenant=self.tenant, property=self.other_owner_property,
            scheduled_at=timezone.now() + timezone.timedelta(days=1), status=Visit.Status.SCHEDULED,
        )
        self.other_owner_pending_visit = Visit.objects.create(
            tenant=self.tenant, property=self.other_owner_property,
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
        )
        self.past_scheduled_visit = Visit.objects.create(
            tenant=self.tenant, property=self.published,
            scheduled_at=timezone.now() - timezone.timedelta(days=1), status=Visit.Status.SCHEDULED,
        )
        self.client.force_login(self.owner)

    def test_access(self):
        response = self.client.get(reverse('dashboard:owner_inquiries'))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('dashboard:owner_visits'))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:owner_inquiries'))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(reverse('dashboard:owner_visits'))
        self.assertEqual(response.status_code, 403)

    def test_inquiries_scoped_to_own_properties_only(self):
        response = self.client.get(reverse('dashboard:owner_inquiries'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['open'], 1)
        self.assertEqual(stats['closed'], 1)
        ids = {i.pk for i in response.context['inquiries']}
        self.assertEqual(ids, {self.open_inquiry.pk, self.closed_inquiry.pk})
        self.assertNotIn(self.other_owner_inquiry.pk, ids)

    def test_close_and_reopen_own_inquiry(self):
        response = self.client.post(
            reverse('dashboard:owner_inquiry_set_status', args=[self.open_inquiry.pk, 'closed']),
        )
        self.assertRedirects(response, reverse('dashboard:owner_inquiries'))
        self.open_inquiry.refresh_from_db()
        self.assertEqual(self.open_inquiry.status, Inquiry.Status.CLOSED)

        response = self.client.post(
            reverse('dashboard:owner_inquiry_set_status', args=[self.open_inquiry.pk, 'open']),
        )
        self.open_inquiry.refresh_from_db()
        self.assertEqual(self.open_inquiry.status, Inquiry.Status.OPEN)

    def test_cannot_change_another_owners_inquiry(self):
        response = self.client.post(
            reverse('dashboard:owner_inquiry_set_status', args=[self.other_owner_inquiry.pk, 'closed']),
        )
        self.assertEqual(response.status_code, 404)
        self.other_owner_inquiry.refresh_from_db()
        self.assertEqual(self.other_owner_inquiry.status, Inquiry.Status.OPEN)

    def test_visits_scoped_to_own_properties_only(self):
        response = self.client.get(reverse('dashboard:owner_visits'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['pending'], 1)
        self.assertEqual(stats['scheduled'], 2)
        ids = {v.pk for v in response.context['visits']}
        self.assertEqual(ids, {self.scheduled_visit.pk, self.pending_visit.pk, self.past_scheduled_visit.pk})
        self.assertNotIn(self.other_owner_visit.pk, ids)
        self.assertNotIn(self.other_owner_pending_visit.pk, ids)

    def test_cancel_own_visit_notifies_tenant(self):
        response = self.client.post(reverse('dashboard:owner_visit_cancel', args=[self.scheduled_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_visits'))
        self.scheduled_visit.refresh_from_db()
        self.assertEqual(self.scheduled_visit.status, Visit.Status.CANCELLED)
        self.assertTrue(Notification.objects.filter(user=self.tenant, message__icontains='cancelled').exists())

    def test_cannot_cancel_another_owners_visit(self):
        response = self.client.post(reverse('dashboard:owner_visit_cancel', args=[self.other_owner_visit.pk]))
        self.assertEqual(response.status_code, 404)
        self.other_owner_visit.refresh_from_db()
        self.assertEqual(self.other_owner_visit.status, Visit.Status.SCHEDULED)

    def test_approve_own_pending_visit_notifies_tenant(self):
        response = self.client.post(reverse('dashboard:owner_visit_approve', args=[self.pending_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_visits'))
        self.pending_visit.refresh_from_db()
        self.assertEqual(self.pending_visit.status, Visit.Status.SCHEDULED)
        self.assertTrue(
            Notification.objects.filter(user=self.other_tenant, message__icontains='confirmed').exists(),
        )

    def test_decline_own_pending_visit_notifies_tenant(self):
        response = self.client.post(reverse('dashboard:owner_visit_decline', args=[self.pending_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_visits'))
        self.pending_visit.refresh_from_db()
        self.assertEqual(self.pending_visit.status, Visit.Status.CANCELLED)
        self.assertTrue(
            Notification.objects.filter(user=self.other_tenant, message__icontains='declined').exists(),
        )

    def test_approve_and_decline_are_no_ops_once_not_pending(self):
        self.client.post(reverse('dashboard:owner_visit_approve', args=[self.scheduled_visit.pk]))
        self.scheduled_visit.refresh_from_db()
        self.assertEqual(self.scheduled_visit.status, Visit.Status.SCHEDULED)

    def test_cannot_approve_or_decline_another_owners_visit(self):
        response = self.client.post(reverse('dashboard:owner_visit_approve', args=[self.other_owner_pending_visit.pk]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('dashboard:owner_visit_decline', args=[self.other_owner_pending_visit.pk]))
        self.assertEqual(response.status_code, 404)
        self.other_owner_pending_visit.refresh_from_db()
        self.assertEqual(self.other_owner_pending_visit.status, Visit.Status.PENDING)

    def test_complete_a_past_scheduled_visit_notifies_tenant(self):
        response = self.client.post(reverse('dashboard:owner_visit_complete', args=[self.past_scheduled_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_visits'))
        self.past_scheduled_visit.refresh_from_db()
        self.assertEqual(self.past_scheduled_visit.status, Visit.Status.COMPLETED)
        self.assertTrue(Notification.objects.filter(user=self.tenant, message__icontains='completed').exists())

    def test_cannot_complete_a_visit_before_its_scheduled_time(self):
        # self.scheduled_visit is scheduled a day in the future — can't
        # honestly be marked completed yet.
        response = self.client.post(reverse('dashboard:owner_visit_complete', args=[self.scheduled_visit.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_visits'))
        self.scheduled_visit.refresh_from_db()
        self.assertEqual(self.scheduled_visit.status, Visit.Status.SCHEDULED)

    def test_cannot_complete_a_pending_visit(self):
        response = self.client.post(reverse('dashboard:owner_visit_complete', args=[self.pending_visit.pk]))
        self.pending_visit.refresh_from_db()
        self.assertEqual(self.pending_visit.status, Visit.Status.PENDING)

    def test_cannot_complete_another_owners_visit(self):
        past_other_owner_visit = Visit.objects.create(
            tenant=self.tenant, property=self.other_owner_property,
            scheduled_at=timezone.now() - timezone.timedelta(days=1), status=Visit.Status.SCHEDULED,
        )
        response = self.client.post(reverse('dashboard:owner_visit_complete', args=[past_other_owner_visit.pk]))
        self.assertEqual(response.status_code, 404)
        past_other_owner_visit.refresh_from_db()
        self.assertEqual(past_other_owner_visit.status, Visit.Status.SCHEDULED)


class AdminSupportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.open_ticket = SupportTicket.objects.create(
            user=self.tenant, subject='Cannot upload photo', category=SupportTicket.Category.PROPERTY,
            description='The upload button does nothing.',
        )
        self.resolved_ticket = SupportTicket.objects.create(
            user=self.tenant, subject='Already fixed', category=SupportTicket.Category.OTHER,
            description='...', status=SupportTicket.Status.RESOLVED,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_support'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_support'))
        self.assertEqual(response.status_code, 403)

    def test_stats_and_status_filter(self):
        response = self.client.get(reverse('dashboard:admin_support'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['open'], 1)
        self.assertEqual(stats['resolved'], 1)

        response = self.client.get(reverse('dashboard:admin_support'), {'status': 'open'})
        ids = [t.pk for t in response.context['tickets']]
        self.assertEqual(ids, [self.open_ticket.pk])

    def test_resolve_notifies_user(self):
        response = self.client.post(
            reverse('dashboard:admin_support_set_status', args=[self.open_ticket.pk, 'resolved']),
        )
        self.assertRedirects(response, reverse('dashboard:admin_support'))
        self.open_ticket.refresh_from_db()
        self.assertEqual(self.open_ticket.status, SupportTicket.Status.RESOLVED)
        self.assertTrue(Notification.objects.filter(user=self.tenant, message__icontains='resolved').exists())


class AdminReportsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        Property.objects.create(owner=self.owner, title='Nagpur Flat', status=Property.Status.PUBLISHED, city='Nagpur')
        Property.objects.create(owner=self.owner, title='Nagpur Flat 2', status=Property.Status.PUBLISHED, city='Nagpur')
        Property.objects.create(owner=self.owner, title='Pune Flat', status=Property.Status.DRAFT, city='Pune')
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_reports'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_reports'))
        self.assertEqual(response.status_code, 403)

    def test_weekly_user_growth_includes_this_week_and_is_zero_filled(self):
        response = self.client.get(reverse('dashboard:admin_reports'))
        user_growth = response.context['user_growth']
        self.assertEqual(len(user_growth), 8)
        # tenant + owner created in setUp both land in the current week bucket
        self.assertEqual(user_growth[-1]['count'], 2)
        self.assertEqual(sum(w['count'] for w in user_growth[:-1]), 0)

    def test_property_status_breakdown_excludes_reserved_statuses(self):
        response = self.client.get(reverse('dashboard:admin_reports'))
        breakdown = {item['label']: item['count'] for item in response.context['property_status_breakdown']}
        self.assertEqual(breakdown.get('Published'), 2)
        self.assertEqual(breakdown.get('Draft'), 1)
        self.assertNotIn('Pending Verification', breakdown)
        self.assertNotIn('Pending Review', breakdown)

    def test_top_cities_reflects_real_property_counts(self):
        response = self.client.get(reverse('dashboard:admin_reports'))
        top_cities = {c['city']: c['count'] for c in response.context['top_cities']}
        self.assertEqual(top_cities.get('Nagpur'), 2)
        self.assertEqual(top_cities.get('Pune'), 1)


class AdminAuditLogTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.property = Property.objects.create(
            owner=self.owner, title='Sunshine Flat', status=Property.Status.PUBLISHED,
            property_type='apartment', city='Nagpur', monthly_rent=15000,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_audit_logs'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_audit_logs'))
        self.assertEqual(response.status_code, 403)

    def test_blocking_a_user_creates_a_log_entry(self):
        self.client.post(reverse('dashboard:admin_user_block', args=[self.tenant.pk]))
        entry = AuditLog.objects.get(target_type='User', target_id=self.tenant.pk)
        self.assertEqual(entry.admin, self.admin)
        self.assertIn('Blocked', entry.message)
        self.assertIn(self.tenant.full_name, entry.message)

    def test_approving_a_property_creates_a_log_entry(self):
        self.client.post(reverse('dashboard:admin_property_approve', args=[self.property.pk]))
        entry = AuditLog.objects.get(target_type='Property', target_id=self.property.pk)
        self.assertIn('Approved', entry.message)
        self.assertIn('Sunshine Flat', entry.message)

    def test_rejecting_a_property_creates_a_log_entry_with_the_reason(self):
        self.client.post(
            reverse('dashboard:admin_property_reject', args=[self.property.pk]), {'reason': 'Bad photos.'},
        )
        entry = AuditLog.objects.get(target_type='Property', target_id=self.property.pk)
        self.assertIn('Rejected', entry.message)
        self.assertIn('Bad photos.', entry.message)

    def test_archiving_a_property_creates_a_log_entry(self):
        self.client.post(reverse('dashboard:admin_property_set_status', args=[self.property.pk, 'archived']))
        entry = AuditLog.objects.get(target_type='Property', target_id=self.property.pk)
        self.assertIn('Archived', entry.message)

    def test_closing_an_inquiry_creates_a_log_entry(self):
        inquiry = Inquiry.objects.create(tenant=self.tenant, property=self.property, message='Hi')
        self.client.post(reverse('dashboard:admin_inquiry_set_status', args=[inquiry.pk, 'closed']))
        entry = AuditLog.objects.get(target_type='Inquiry', target_id=inquiry.pk)
        self.assertIn('Closed', entry.message)

    def test_cancelling_a_visit_creates_a_log_entry(self):
        visit = Visit.objects.create(
            tenant=self.tenant, property=self.property, scheduled_at=timezone.now() + timezone.timedelta(days=1),
        )
        self.client.post(reverse('dashboard:admin_visit_cancel', args=[visit.pk]))
        entry = AuditLog.objects.get(target_type='Visit', target_id=visit.pk)
        self.assertIn('Cancelled', entry.message)

    def test_resolving_a_ticket_creates_a_log_entry(self):
        ticket = SupportTicket.objects.create(user=self.tenant, subject='Help', description='...')
        self.client.post(reverse('dashboard:admin_support_set_status', args=[ticket.pk, 'resolved']))
        entry = AuditLog.objects.get(target_type='SupportTicket', target_id=ticket.pk)
        self.assertIn('Resolved', entry.message)

    def test_stats_and_search_filter(self):
        AuditLog.objects.create(admin=self.admin, message='Blocked user Someone', target_type='User')
        AuditLog.objects.create(admin=self.admin, message='Approved property "X"', target_type='Property')

        response = self.client.get(reverse('dashboard:admin_audit_logs'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['today'], 2)
        self.assertEqual(stats['this_week'], 2)

        response = self.client.get(reverse('dashboard:admin_audit_logs'), {'target_type': 'Property'})
        messages_shown = [log.message for log in response.context['logs']]
        self.assertEqual(messages_shown, ['Approved property "X"'])

    def test_log_is_append_only_in_django_admin(self):
        from .admin import AuditLogAdmin
        model_admin = AuditLogAdmin(AuditLog, None)
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))


class AdminCmsFaqTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.faq = FAQ.objects.create(
            question='Existing question', answer='Existing answer.', placement=FAQ.Placement.CONTACT,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_cms'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_cms'))
        self.assertEqual(response.status_code, 403)

    def test_website_pages_table_lists_every_public_page(self):
        response = self.client.get(reverse('dashboard:admin_cms'))
        titles = [p['title'] for p in response.context['pages']]
        self.assertEqual(titles, ['Home', 'About Us', 'Contact Us', 'Become a Host', 'Terms & Conditions', 'Privacy Policy'])

    def test_website_pages_last_updated_reflects_real_content_timestamp(self):
        # The seed migrations already gave every page real ContentBlock/FAQ/
        # LegalPage rows, so every page should resolve a real timestamp —
        # never a fabricated one.
        response = self.client.get(reverse('dashboard:admin_cms'))
        for page in response.context['pages']:
            self.assertIsNotNone(page['updated_at'], f'{page["title"]} has no real timestamp source')

    def test_website_pages_manage_link_prefilters_correctly(self):
        response = self.client.get(reverse('dashboard:admin_cms'))
        pages_by_title = {p['title']: p for p in response.context['pages']}
        self.assertIn('placement=home_why_choose', pages_by_title['Home']['manage_url'])
        self.assertIn('placement=contact', pages_by_title['Contact Us']['manage_url'])

    def test_create_faq(self):
        response = self.client.post(reverse('dashboard:admin_cms_faq_add'), {
            'question': 'New question?', 'answer': 'New answer.',
            'placement': FAQ.Placement.TENANT_HELP, 'order': 0, 'is_published': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:admin_cms'))
        self.assertTrue(FAQ.objects.filter(question='New question?', placement=FAQ.Placement.TENANT_HELP).exists())

    def test_edit_faq(self):
        response = self.client.post(reverse('dashboard:admin_cms_faq_edit', args=[self.faq.pk]), {
            'question': 'Updated question', 'answer': 'Updated answer.',
            'placement': FAQ.Placement.CONTACT, 'order': 5, 'is_published': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:admin_cms'))
        self.faq.refresh_from_db()
        self.assertEqual(self.faq.question, 'Updated question')
        self.assertEqual(self.faq.order, 5)

    def test_toggle_publish(self):
        self.assertTrue(self.faq.is_published)
        response = self.client.post(reverse('dashboard:admin_cms_faq_toggle', args=[self.faq.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_cms'))
        self.faq.refresh_from_db()
        self.assertFalse(self.faq.is_published)

    def test_delete_faq(self):
        response = self.client.post(reverse('dashboard:admin_cms_faq_delete', args=[self.faq.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_cms'))
        self.assertFalse(FAQ.objects.filter(pk=self.faq.pk).exists())

    def test_search_and_placement_filter(self):
        FAQ.objects.create(question='Tenant one', answer='...', placement=FAQ.Placement.TENANT_HELP)
        response = self.client.get(reverse('dashboard:admin_cms'), {'q': 'Existing'})
        questions = [f.question for f in response.context['faqs']]
        self.assertEqual(questions, ['Existing question'])

        response = self.client.get(reverse('dashboard:admin_cms'), {'q': 'Tenant one', 'placement': 'tenant_help'})
        questions = [f.question for f in response.context['faqs']]
        self.assertEqual(questions, ['Tenant one'])

    def test_faq_actions_are_logged(self):
        self.client.post(reverse('dashboard:admin_cms_faq_toggle', args=[self.faq.pk]))
        self.assertTrue(AuditLog.objects.filter(target_type='FAQ', target_id=self.faq.pk).exists())


class AdminCmsContentBlockTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.block = ContentBlock.objects.create(
            placement=ContentBlock.Placement.HOME_WHY_CHOOSE, icon='heart',
            title='Existing block', text='Existing text.',
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_content_blocks'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_content_blocks'))
        self.assertEqual(response.status_code, 403)

    def test_create_block(self):
        response = self.client.post(reverse('dashboard:admin_content_block_add'), {
            'placement': ContentBlock.Placement.HOST_PERKS, 'icon': 'star',
            'title': 'New perk', 'text': 'New perk text.', 'order': 0, 'is_published': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:admin_content_blocks'))
        self.assertTrue(ContentBlock.objects.filter(title='New perk', placement=ContentBlock.Placement.HOST_PERKS).exists())

    def test_edit_block(self):
        response = self.client.post(reverse('dashboard:admin_content_block_edit', args=[self.block.pk]), {
            'placement': ContentBlock.Placement.HOME_WHY_CHOOSE, 'icon': 'heart',
            'title': 'Updated block', 'text': 'Updated text.', 'order': 3, 'is_published': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:admin_content_blocks'))
        self.block.refresh_from_db()
        self.assertEqual(self.block.title, 'Updated block')
        self.assertEqual(self.block.order, 3)

    def test_toggle_publish(self):
        self.assertTrue(self.block.is_published)
        response = self.client.post(reverse('dashboard:admin_content_block_toggle', args=[self.block.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_content_blocks'))
        self.block.refresh_from_db()
        self.assertFalse(self.block.is_published)

    def test_delete_block(self):
        response = self.client.post(reverse('dashboard:admin_content_block_delete', args=[self.block.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_content_blocks'))
        self.assertFalse(ContentBlock.objects.filter(pk=self.block.pk).exists())

    def test_block_actions_are_logged(self):
        self.client.post(reverse('dashboard:admin_content_block_toggle', args=[self.block.pk]))
        self.assertTrue(AuditLog.objects.filter(target_type='ContentBlock', target_id=self.block.pk).exists())


class AdminCmsLegalPageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        # The 0006_seed_legal_pages data migration already created a 'terms'
        # row (LegalPage.slug is unique) — fetch it rather than creating a
        # second one.
        self.page = LegalPage.objects.get(slug='terms')
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_legal_pages'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_legal_pages'))
        self.assertEqual(response.status_code, 403)

    def test_edit_legal_page(self):
        response = self.client.post(reverse('dashboard:admin_legal_page_edit', args=[self.page.pk]), {
            'title': 'Terms & Conditions', 'body': 'Updated body text.',
        })
        self.assertRedirects(response, reverse('dashboard:admin_legal_pages'))
        self.page.refresh_from_db()
        self.assertEqual(self.page.body, 'Updated body text.')

    def test_edit_is_logged(self):
        self.client.post(reverse('dashboard:admin_legal_page_edit', args=[self.page.pk]), {
            'title': 'Terms & Conditions', 'body': 'Updated again.',
        })
        self.assertTrue(AuditLog.objects.filter(target_type='LegalPage', target_id=self.page.pk).exists())


class AdminCmsSiteSettingsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_site_settings'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_site_settings'))
        self.assertEqual(response.status_code, 403)

    def test_update_settings(self):
        response = self.client.post(reverse('dashboard:admin_site_settings'), {
            'platform_name': 'Rentora',
            'support_phone': '+91 90000 00000', 'support_email': 'help@rentora.local',
            'business_address': '', 'facebook_url': 'https://facebook.com/rentora',
            'instagram_url': '', 'twitter_url': '', 'linkedin_url': '',
        })
        self.assertRedirects(response, reverse('dashboard:admin_site_settings'))
        settings_obj = SiteSettings.load()
        self.assertEqual(settings_obj.support_phone, '+91 90000 00000')
        self.assertEqual(settings_obj.facebook_url, 'https://facebook.com/rentora')

    def test_settings_stay_a_singleton(self):
        SiteSettings.load()
        self.client.post(reverse('dashboard:admin_site_settings'), {
            'platform_name': 'Rentora',
            'support_phone': '+91 90000 00000', 'support_email': '', 'business_address': '',
            'facebook_url': '', 'instagram_url': '', 'twitter_url': '', 'linkedin_url': '',
        })
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_update_platform_name_and_it_appears_sitewide(self):
        self.client.post(reverse('dashboard:admin_site_settings'), {
            'platform_name': 'RentHub',
            'support_phone': '', 'support_email': '', 'business_address': '',
            'facebook_url': '', 'instagram_url': '', 'twitter_url': '', 'linkedin_url': '',
        })
        self.assertEqual(SiteSettings.load().platform_name, 'RentHub')


class AdminSeoSettingsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_seo_settings'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_seo_settings'))
        self.assertEqual(response.status_code, 403)

    def test_hub_lists_every_seeded_page(self):
        response = self.client.get(reverse('dashboard:admin_seo_settings'))
        pages = [p.page for p in response.context['pages']]
        self.assertEqual(set(pages), {'home', 'about', 'contact', 'become_host', 'terms', 'privacy'})

    def test_update_analytics_ids(self):
        response = self.client.post(reverse('dashboard:admin_seo_settings'), {
            'google_analytics_id': 'G-ABC123', 'facebook_pixel_id': '',
        })
        self.assertRedirects(response, reverse('dashboard:admin_seo_settings'))
        self.assertEqual(SiteSettings.load().google_analytics_id, 'G-ABC123')

    def test_edit_page_meta(self):
        page_seo = PageSEO.objects.get(page=PageSEO.Page.HOME)
        response = self.client.post(reverse('dashboard:admin_page_seo_edit', args=[page_seo.pk]), {
            'meta_title': 'New Home Title', 'meta_description': 'New description.',
        })
        self.assertRedirects(response, reverse('dashboard:admin_seo_settings'))
        page_seo.refresh_from_db()
        self.assertEqual(page_seo.meta_title, 'New Home Title')

    def test_page_meta_edit_is_logged(self):
        page_seo = PageSEO.objects.get(page=PageSEO.Page.HOME)
        self.client.post(reverse('dashboard:admin_page_seo_edit', args=[page_seo.pk]), {
            'meta_title': 'New Home Title', 'meta_description': 'New description.',
        })
        self.assertTrue(AuditLog.objects.filter(target_type='PageSEO', target_id=page_seo.pk).exists())


class AdminSubscriptionsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.plan = SubscriptionPlan.objects.get(name='Silver')
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_subscriptions'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_subscriptions'))
        self.assertEqual(response.status_code, 403)

    def test_stats_reflect_seeded_plans(self):
        response = self.client.get(reverse('dashboard:admin_subscriptions'))
        self.assertEqual(response.context['stats']['total'], 4)
        self.assertEqual(response.context['stats']['active'], 4)

    def test_create_plan(self):
        response = self.client.post(reverse('dashboard:admin_subscription_plan_add'), {
            'name': 'Enterprise', 'price': '4999', 'listing_limit': '', 'order': 4, 'is_active': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:admin_subscriptions'))
        self.assertTrue(SubscriptionPlan.objects.filter(name='Enterprise', listing_limit=None).exists())

    def test_edit_plan(self):
        response = self.client.post(reverse('dashboard:admin_subscription_plan_edit', args=[self.plan.pk]), {
            'name': 'Silver', 'price': '599', 'listing_limit': '15', 'order': 1, 'is_active': 'on',
        })
        self.assertRedirects(response, reverse('dashboard:admin_subscriptions'))
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.price, 599)
        self.assertEqual(self.plan.listing_limit, 15)

    def test_toggle_active(self):
        self.assertTrue(self.plan.is_active)
        response = self.client.post(reverse('dashboard:admin_subscription_plan_toggle', args=[self.plan.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_subscriptions'))
        self.plan.refresh_from_db()
        self.assertFalse(self.plan.is_active)

    def test_plan_changes_are_logged(self):
        self.client.post(reverse('dashboard:admin_subscription_plan_toggle', args=[self.plan.pk]))
        self.assertTrue(AuditLog.objects.filter(target_type='SubscriptionPlan', target_id=self.plan.pk).exists())


class AdminPaymentsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123',
            full_name='Test Owner', role=User.Role.OWNER,
        )
        plan = SubscriptionPlan.objects.get(name='Gold')
        Payment.objects.create(
            owner=self.owner, plan=plan, razorpay_order_id='order_1', amount=plan.price,
            status=Payment.Status.PAID,
        )
        Payment.objects.create(
            owner=self.owner, plan=plan, razorpay_order_id='order_2', amount=plan.price,
            status=Payment.Status.FAILED,
        )
        self.client.force_login(self.admin)

    def test_access(self):
        response = self.client.get(reverse('dashboard:admin_payments'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:admin_payments'))
        self.assertEqual(response.status_code, 403)

    def test_stats_and_status_filter(self):
        response = self.client.get(reverse('dashboard:admin_payments'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['paid'], 1)
        self.assertEqual(stats['failed'], 1)

        response = self.client.get(reverse('dashboard:admin_payments'), {'status': 'paid'})
        order_ids = [p.razorpay_order_id for p in response.context['payments']]
        self.assertEqual(order_ids, ['order_1'])


class AdminInternalUsersTests(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            email='super-admin@example.com', password='AdminPass123',
            full_name='Test Super Admin', role=User.Role.SUPER_ADMIN,
        )
        self.other_super_admin = User.objects.create_user(
            email='super-admin-2@example.com', password='AdminPass123',
            full_name='Other Super Admin', role=User.Role.SUPER_ADMIN,
        )
        self.admin = User.objects.create_user(
            email='admin@example.com', password='AdminPass123',
            full_name='Test Admin', role=User.Role.ADMIN,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )
        self.client.force_login(self.super_admin)

    def test_access_is_super_admin_only(self):
        response = self.client.get(reverse('dashboard:admin_internal_users'))
        self.assertEqual(response.status_code, 200)

        for user in (self.admin, self.tenant):
            self.client.force_login(user)
            response = self.client.get(reverse('dashboard:admin_internal_users'))
            self.assertEqual(response.status_code, 403)

    def test_stats(self):
        response = self.client.get(reverse('dashboard:admin_internal_users'))
        stats = response.context['stats']
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['active'], 3)
        self.assertEqual(stats['super_admins'], 2)

    def test_create_admin_account_is_real_and_usable(self):
        response = self.client.post(reverse('dashboard:admin_user_create'), {
            'full_name': 'New Admin', 'email': 'new-admin@example.com', 'mobile_number': '',
            'role': User.Role.ADMIN, 'password1': 'NewAdminPass456', 'password2': 'NewAdminPass456',
        })
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        new_admin = User.objects.get(email='new-admin@example.com')
        self.assertEqual(new_admin.role, User.Role.ADMIN)
        self.assertFalse(new_admin.is_staff)
        self.assertFalse(new_admin.is_superuser)
        self.client.logout()
        self.assertTrue(self.client.login(email='new-admin@example.com', password='NewAdminPass456'))

    def test_create_admin_rejects_mismatched_passwords(self):
        response = self.client.post(reverse('dashboard:admin_user_create'), {
            'full_name': 'New Admin', 'email': 'new-admin@example.com', 'mobile_number': '',
            'role': User.Role.ADMIN, 'password1': 'NewAdminPass456', 'password2': 'Different789',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='new-admin@example.com').exists())

    def test_promote_and_demote_role(self):
        response = self.client.post(reverse('dashboard:admin_user_set_role_super_admin', args=[self.admin.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, User.Role.SUPER_ADMIN)

        response = self.client.post(reverse('dashboard:admin_user_set_role_admin', args=[self.admin.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, User.Role.ADMIN)

    def test_cannot_change_own_role(self):
        response = self.client.post(reverse('dashboard:admin_user_set_role_admin', args=[self.super_admin.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        self.super_admin.refresh_from_db()
        self.assertEqual(self.super_admin.role, User.Role.SUPER_ADMIN)

    def test_activate_and_deactivate(self):
        response = self.client.post(reverse('dashboard:admin_internal_user_deactivate', args=[self.admin.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_active)
        self.assertFalse(self.client.login(email='admin@example.com', password='AdminPass123'))

        response = self.client.post(reverse('dashboard:admin_internal_user_activate', args=[self.admin.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_cannot_deactivate_self(self):
        response = self.client.post(reverse('dashboard:admin_internal_user_deactivate', args=[self.super_admin.pk]))
        self.assertRedirects(response, reverse('dashboard:admin_internal_users'))
        self.super_admin.refresh_from_db()
        self.assertTrue(self.super_admin.is_active)

    def test_last_active_super_admin_helper(self):
        # The "last active super admin" guard can never actually trigger
        # through this app's own web UI in a single-actor-per-request model:
        # the actor must themselves be an active super admin to pass
        # @super_admin_required, and self-action is already blocked
        # separately — so a *different* actor demoting/deactivating a
        # *different* target always leaves at least one (the actor) active.
        # The guard exists as defense-in-depth against other pathways (e.g.
        # Django's own /admin/ site, which can edit is_active directly and
        # isn't restricted by this app's checks) — tested directly here.
        from .views import _is_last_active_super_admin
        self.other_super_admin.is_active = False
        self.other_super_admin.save(update_fields=['is_active'])
        self.assertTrue(_is_last_active_super_admin(self.super_admin))

        self.other_super_admin.is_active = True
        self.other_super_admin.save(update_fields=['is_active'])
        self.assertFalse(_is_last_active_super_admin(self.super_admin))

    def test_admin_user_actions_are_logged(self):
        self.client.post(reverse('dashboard:admin_user_set_role_super_admin', args=[self.admin.pk]))
        self.assertTrue(AuditLog.objects.filter(target_type='User', target_id=self.admin.pk).exists())


class OwnerAdminBookingsTests(TestCase):
    """Feature 26 — the Hotel Booking flow. bookings/tests.py covers the
    tenant-facing request/list/cancel actions; this covers the owner-side
    Confirm/Decline and the platform-wide admin oversight list."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com', password='StrongPass123', full_name='Owner', role=User.Role.OWNER,
        )
        self.other_owner = User.objects.create_user(
            email='owner2@example.com', password='StrongPass123', full_name='Other Owner', role=User.Role.OWNER,
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123', full_name='Tenant', role=User.Role.TENANT,
        )
        self.hotel = Property.objects.create(
            owner=self.owner, title='Lakeview Homestay', status=Property.Status.PUBLISHED,
            category=Property.Category.HOMESTAY, city='Nagpur', nightly_rate=2000,
        )
        self.other_owner_hotel = Property.objects.create(
            owner=self.other_owner, title='Other Homestay', status=Property.Status.PUBLISHED,
            category=Property.Category.HOMESTAY, city='Nagpur', nightly_rate=1500,
        )
        self.pending = Booking.objects.create(
            tenant=self.tenant, property=self.hotel,
            check_in=date.today() + timedelta(days=5), check_out=date.today() + timedelta(days=8),
        )
        self.other_owner_booking = Booking.objects.create(
            tenant=self.tenant, property=self.other_owner_hotel,
            check_in=date.today() + timedelta(days=5), check_out=date.today() + timedelta(days=8),
        )
        self.client.force_login(self.owner)

    def test_owner_bookings_access(self):
        response = self.client.get(reverse('dashboard:owner_bookings'))
        self.assertEqual(response.status_code, 200)
        self.client.force_login(self.tenant)
        response = self.client.get(reverse('dashboard:owner_bookings'))
        self.assertEqual(response.status_code, 403)

    def test_bookings_scoped_to_own_properties_only(self):
        response = self.client.get(reverse('dashboard:owner_bookings'))
        ids = {b.pk for b in response.context['bookings']}
        self.assertEqual(ids, {self.pending.pk})
        self.assertNotIn(self.other_owner_booking.pk, ids)

    def test_owner_confirms_a_pending_booking(self):
        response = self.client.post(reverse('dashboard:owner_booking_confirm', args=[self.pending.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_bookings'))
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Booking.Status.CONFIRMED)
        self.assertTrue(self.tenant.notifications.filter(category='visit', message__icontains='confirmed').exists())

    def test_owner_declines_a_pending_booking(self):
        response = self.client.post(reverse('dashboard:owner_booking_decline', args=[self.pending.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_bookings'))
        self.pending.refresh_from_db()
        self.assertEqual(self.pending.status, Booking.Status.DECLINED)
        self.assertTrue(self.tenant.notifications.filter(category='visit', message__icontains='declined').exists())

    def test_cannot_confirm_another_owners_booking(self):
        response = self.client.post(reverse('dashboard:owner_booking_confirm', args=[self.other_owner_booking.pk]))
        self.assertEqual(response.status_code, 404)
        self.other_owner_booking.refresh_from_db()
        self.assertEqual(self.other_owner_booking.status, Booking.Status.PENDING)

    def test_confirming_a_booking_that_overlaps_an_already_confirmed_one_is_blocked(self):
        other_tenant = User.objects.create_user(
            email='tenant2@example.com', password='StrongPass123', full_name='Tenant Two', role=User.Role.TENANT,
        )
        overlapping = Booking.objects.create(
            tenant=other_tenant, property=self.hotel,
            check_in=date.today() + timedelta(days=6), check_out=date.today() + timedelta(days=7),
        )
        self.pending.status = Booking.Status.CONFIRMED
        self.pending.save(update_fields=['status'])

        response = self.client.post(reverse('dashboard:owner_booking_confirm', args=[overlapping.pk]))
        self.assertRedirects(response, reverse('dashboard:owner_bookings'))
        overlapping.refresh_from_db()
        self.assertEqual(overlapping.status, Booking.Status.PENDING)

    def test_admin_bookings_lists_every_booking_platform_wide(self):
        admin = User.objects.create_user(
            email='admin@example.com', password='StrongPass123', full_name='Admin', role=User.Role.ADMIN,
        )
        self.client.force_login(admin)
        response = self.client.get(reverse('dashboard:admin_bookings'))
        self.assertEqual(response.status_code, 200)
        ids = {b.pk for b in response.context['bookings']}
        self.assertEqual(ids, {self.pending.pk, self.other_owner_booking.pk})

    def test_admin_bookings_requires_admin_role(self):
        response = self.client.get(reverse('dashboard:admin_bookings'))
        self.assertEqual(response.status_code, 403)
