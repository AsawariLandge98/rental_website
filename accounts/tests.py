from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import MobileOTP, User

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
        cache.clear()  # login-attempt lockout state is process-global, not per-test
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
        cache.clear()  # login-attempt lockout state is process-global, not per-test
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


class LoginRateLimitTests(TestCase):
    """Real brute-force lockout — previously nothing throttled repeated
    password guesses on either login form at all."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT,
        )

    def _wrong_attempt(self):
        return self.client.post('/accounts/login/', {
            'email': 'tenant@example.com', 'password': 'WrongPass999',
        })

    def test_locks_out_after_five_failed_attempts(self):
        for _ in range(5):
            response = self._wrong_attempt()
            self.assertContains(response, 'Invalid email or password')

        # The 6th attempt is blocked before authentication even runs —
        # correct password included, to prove it's the lockout, not a typo.
        response = self.client.post('/accounts/login/', {
            'email': 'tenant@example.com', 'password': 'StrongPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many failed login attempts')

    def test_successful_login_resets_the_counter(self):
        for _ in range(4):
            self._wrong_attempt()
        response = self.client.post('/accounts/login/', {
            'email': 'tenant@example.com', 'password': 'StrongPass123',
        })
        self.assertRedirects(response, '/tenant/dashboard/')

        self.client.logout()
        # A fresh wrong attempt right after a successful login should not
        # be treated as the 5th of the earlier run — the counter was
        # cleared on success.
        response = self._wrong_attempt()
        self.assertContains(response, 'Invalid email or password')
        self.assertNotContains(response, 'Too many failed login attempts')

    def test_lockout_applies_to_admin_login_too(self):
        # Same IP, same shared cache key — five failures on the public
        # login form should also lock out the internal admin login.
        admin = User.objects.create_superuser(
            email='admin@example.com', password='AdminPass123', full_name='Admin',
        )
        for _ in range(5):
            self._wrong_attempt()
        response = self.client.post('/accounts/internal-login/', {
            'email': 'admin@example.com', 'password': 'AdminPass123', 'role': 'super_admin',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many failed login attempts')


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


class GoogleSignInTests(TestCase):
    """Real credentials are blank in dev/test, so google_login_start should
    honestly refuse rather than pretend to work — this is exactly what
    settings.GOOGLE_OAUTH_CONFIGURED exists to control."""

    def test_google_login_start_redirects_to_register_when_not_configured(self):
        response = self.client.get('/accounts/google/', {'type': 'owner'})
        self.assertRedirects(response, '/accounts/register/')

    def test_google_login_start_does_not_stash_invalid_role(self):
        self.client.get('/accounts/google/', {'type': 'admin'})
        self.assertNotIn('social_signup_role', self.client.session)


class CompleteProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='googleuser@example.com', full_name='Google User', role=User.Role.OWNER,
        )
        self.user.set_unusable_password()
        self.user.save()

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get('/accounts/complete-profile/')
        self.assertRedirects(response, '/accounts/login/')

    def test_valid_submission_saves_name_and_dob_and_redirects_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.post('/accounts/complete-profile/', {
            'full_name': 'Google User Updated', 'date_of_birth': '1995-06-15',
        })
        self.assertRedirects(response, '/owner/dashboard/')
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Google User Updated')
        self.assertEqual(str(self.user.date_of_birth), '1995-06-15')

    def test_underage_date_of_birth_rejected(self):
        self.client.force_login(self.user)
        from datetime import date, timedelta
        too_young = (date.today() - timedelta(days=17 * 365)).isoformat()
        response = self.client.post('/accounts/complete-profile/', {
            'full_name': 'Google User', 'date_of_birth': too_young,
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.date_of_birth)

    def test_blank_full_name_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post('/accounts/complete-profile/', {
            'full_name': '', 'date_of_birth': '1995-06-15',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.date_of_birth)


def _digit_payload(code):
    return {f'digit{i + 1}': digit for i, digit in enumerate(code)}


class MobileVerificationTests(TestCase):
    """Feature 24 — self-service Mobile OTP verification. SMS_CONFIGURED
    is False in the test environment (no real .env values loaded here), so
    most tests exercise the dev-mode path where the code is surfaced via a
    Django message instead of actually being texted."""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            email='tenant@example.com', password='StrongPass123',
            full_name='Test Tenant', role=User.Role.TENANT, mobile_number='9876543210',
        )
        self.client.force_login(self.user)

    def _sent_code(self):
        otp = MobileOTP.objects.filter(user=self.user, is_used=False).latest('created_at')
        return otp.code

    def test_send_and_confirm_require_login(self):
        self.client.logout()
        response = self.client.post('/accounts/mobile/verify/send/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        response = self.client.get('/accounts/mobile/verify/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_send_without_mobile_number_on_file_is_rejected(self):
        self.user.mobile_number = ''
        self.user.save(update_fields=['mobile_number'])
        response = self.client.post('/accounts/mobile/verify/send/', follow=True)
        self.assertContains(response, 'Add a mobile number')
        self.assertFalse(MobileOTP.objects.filter(user=self.user).exists())

    def test_already_verified_user_is_told_so_and_no_code_is_generated(self):
        self.user.is_mobile_verified = True
        self.user.save(update_fields=['is_mobile_verified'])
        response = self.client.post('/accounts/mobile/verify/send/', follow=True)
        self.assertContains(response, 'already verified')
        self.assertFalse(MobileOTP.objects.filter(user=self.user).exists())

    def test_send_dev_mode_creates_otp_and_shows_code_in_message(self):
        response = self.client.post('/accounts/mobile/verify/send/', follow=True)
        self.assertRedirects(response, '/accounts/mobile/verify/', target_status_code=200)
        otp = MobileOTP.objects.get(user=self.user)
        self.assertEqual(len(otp.code), 6)
        self.assertContains(response, otp.code)
        self.assertContains(response, 'dev mode')

    def test_resend_immediately_is_blocked_by_cooldown(self):
        self.client.post('/accounts/mobile/verify/send/')
        first_otp_id = MobileOTP.objects.get(user=self.user).id
        response = self.client.post('/accounts/mobile/verify/send/', follow=True)
        self.assertContains(response, 'wait a minute')
        # No second OTP row was created — the original is still the only one.
        self.assertEqual(MobileOTP.objects.filter(user=self.user).count(), 1)
        self.assertEqual(MobileOTP.objects.get(user=self.user).id, first_otp_id)

    def test_resending_after_cooldown_invalidates_the_previous_code(self):
        self.client.post('/accounts/mobile/verify/send/')
        first_code = self._sent_code()
        cache.clear()  # simulate cooldown having expired
        self.client.post('/accounts/mobile/verify/send/')
        second_code = self._sent_code()
        first_otp = MobileOTP.objects.get(code=first_code)
        self.assertTrue(first_otp.is_used)
        self.assertNotEqual(first_code, second_code)

    def test_correct_code_verifies_the_mobile_number(self):
        self.client.post('/accounts/mobile/verify/send/')
        code = self._sent_code()
        response = self.client.post('/accounts/mobile/verify/', _digit_payload(code), follow=True)
        self.assertContains(response, 'verified')
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_mobile_verified)

    def test_incorrect_code_does_not_verify_and_shows_error(self):
        self.client.post('/accounts/mobile/verify/send/')
        real_code = self._sent_code()
        wrong_code = '000000' if real_code != '000000' else '111111'
        response = self.client.post('/accounts/mobile/verify/', _digit_payload(wrong_code), follow=True)
        self.assertContains(response, 'Incorrect code')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_mobile_verified)

    def test_too_many_wrong_attempts_invalidates_the_code(self):
        self.client.post('/accounts/mobile/verify/send/')
        real_code = self._sent_code()
        wrong_code = '000000' if real_code != '000000' else '111111'
        for _ in range(MobileOTP.MAX_ATTEMPTS):
            self.client.post('/accounts/mobile/verify/', _digit_payload(wrong_code))
        otp = MobileOTP.objects.get(code=real_code)
        self.assertTrue(otp.is_used)
        # Even the correct code no longer works once the row is spent.
        response = self.client.post('/accounts/mobile/verify/', _digit_payload(real_code), follow=True)
        self.assertContains(response, 'expired or is no longer valid')
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_mobile_verified)

    @override_settings(SMS_CONFIGURED=True)
    @patch('accounts.views.send_sms')
    def test_configured_gateway_is_used_and_code_is_not_leaked_in_the_response(self, mock_send_sms):
        response = self.client.post('/accounts/mobile/verify/send/', follow=True)
        otp = MobileOTP.objects.get(user=self.user)
        mock_send_sms.assert_called_once()
        self.assertEqual(mock_send_sms.call_args[0][0], self.user.mobile_number)
        self.assertIn(otp.code, mock_send_sms.call_args[0][1])
        self.assertNotContains(response, otp.code)
        self.assertNotContains(response, 'dev mode')

    @override_settings(SMS_CONFIGURED=True)
    @patch('accounts.views.send_sms')
    def test_gateway_failure_is_handled_gracefully(self, mock_send_sms):
        from core.sms import SMSSendError
        mock_send_sms.side_effect = SMSSendError('gateway down')
        response = self.client.post('/accounts/mobile/verify/send/', follow=True)
        self.assertContains(response, 'send the SMS right now')
        self.assertTrue(MobileOTP.objects.filter(user=self.user).exists())
