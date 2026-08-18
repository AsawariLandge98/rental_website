from django.core import mail
from django.test import TestCase

from .models import User

REGISTER_DATA = {
    'role': 'tenant',
    'full_name': 'Test Tenant',
    'mobile_number': '9876543210',
    'email': 'tenant@example.com',
    'password': 'StrongPass123',
    'confirm_password': 'StrongPass123',
    'accept_terms': 'on',
}


class RegistrationTests(TestCase):
    def test_register_creates_user_logs_in_and_redirects_to_role_dashboard(self):
        response = self.client.post('/accounts/register/', REGISTER_DATA)
        self.assertRedirects(response, '/tenant/dashboard/')
        user = User.objects.get(email='tenant@example.com')
        self.assertEqual(user.role, User.Role.TENANT)
        self.assertTrue(user.check_password('StrongPass123'))

    def test_duplicate_email_is_rejected(self):
        self.client.post('/accounts/register/', REGISTER_DATA)
        # A fresh, logged-out client: the first client is now authenticated
        # as the user it just created, and the register view redirects
        # already-authenticated visitors straight to their dashboard.
        response = self.client_class().post('/accounts/register/', REGISTER_DATA)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already exists')
        self.assertEqual(User.objects.filter(email='tenant@example.com').count(), 1)

    def test_mismatched_passwords_are_rejected(self):
        data = {**REGISTER_DATA, 'confirm_password': 'Different123'}
        response = self.client.post('/accounts/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match')

    def test_owner_and_hotel_roles_redirect_to_their_own_dashboards(self):
        for role, path in [('owner', '/owner/dashboard/'), ('hotel', '/hotel/dashboard/')]:
            data = {**REGISTER_DATA, 'role': role, 'email': f'{role}@example.com'}
            response = self.client_class().post('/accounts/register/', data)
            self.assertRedirects(response, path)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def test_correct_credentials_log_in_and_redirect_to_dashboard(self):
        response = self.client.post('/accounts/login/', {
            'email': 'tenant@example.com', 'password': 'StrongPass123',
        })
        self.assertRedirects(response, '/tenant/dashboard/')

    def test_wrong_password_shows_generic_error(self):
        response = self.client.post('/accounts/login/', {
            'email': 'tenant@example.com', 'password': 'WrongPass999',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')

    def test_dashboard_requires_login(self):
        response = self.client.get('/tenant/dashboard/')
        self.assertRedirects(response, '/accounts/login/?next=/tenant/dashboard/')

    def test_cannot_access_another_roles_dashboard(self):
        self.client.login(email='tenant@example.com', password='StrongPass123')
        response = self.client.get('/owner/dashboard/')
        self.assertEqual(response.status_code, 403)

    def test_logout_ends_session(self):
        self.client.login(email='tenant@example.com', password='StrongPass123')
        self.client.post('/accounts/logout/')
        response = self.client.get('/tenant/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)


class InternalLoginTests(TestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            email='admin@example.com', password='AdminPass123', full_name='Super Admin',
        )
        self.tenant = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def test_super_admin_can_log_in_and_is_redirected(self):
        response = self.client.post('/accounts/internal-login/', {
            'email': 'admin@example.com', 'password': 'AdminPass123', 'role': 'super_admin',
        })
        self.assertRedirects(response, '/super-admin/dashboard/')

    def test_public_user_cannot_use_internal_login(self):
        response = self.client.post('/accounts/internal-login/', {
            'email': 'tenant@example.com', 'password': 'StrongPass123', 'role': 'admin',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')

    def test_role_tab_must_match_account_role(self):
        response = self.client.post('/accounts/internal-login/', {
            'email': 'admin@example.com', 'password': 'AdminPass123', 'role': 'admin',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')


class ForgotPasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='tenant@example.com', password='OldPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def test_reset_flow_changes_password_and_invalidates_old_password(self):
        self.client.post('/accounts/forgot-password/', {'email': 'tenant@example.com'})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/accounts/reset/', mail.outbox[0].body)

        import re
        match = re.search(r'/accounts/reset/\S+/', mail.outbox[0].body)
        reset_path = match.group(0)

        response = self.client.get(reset_path)
        set_password_url = response.url
        response = self.client.post(set_password_url, {
            'new_password1': 'NewPass456', 'new_password2': 'NewPass456',
        })
        self.assertRedirects(response, '/accounts/reset/done/')

        self.assertFalse(self.client.login(email='tenant@example.com', password='OldPass123'))
        self.assertTrue(self.client.login(email='tenant@example.com', password='NewPass456'))

    def test_reset_link_cannot_be_reused_after_password_is_changed(self):
        self.client.post('/accounts/forgot-password/', {'email': 'tenant@example.com'})
        import re
        match = re.search(r'/accounts/reset/\S+/', mail.outbox[0].body)
        reset_path = match.group(0)

        response = self.client.get(reset_path)
        set_password_url = response.url
        self.client.post(set_password_url, {
            'new_password1': 'NewPass456', 'new_password2': 'NewPass456',
        })

        # The token is derived from the user's password hash, so it stops
        # validating once the password has actually been changed.
        fresh_client = self.client_class()
        response = fresh_client.get(reset_path)
        response = fresh_client.get(response.url if response.status_code == 302 else reset_path)
        self.assertContains(response, 'Link Expired')
