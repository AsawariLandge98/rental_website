# Feature 21 — Real SMTP Email Sending

## Context

Next item off the "high priority, not yet built" list — the site's only real email-sending code path (Django's built-in password-reset flow, `accounts/views.py::ForgotPasswordView`) had `EMAIL_BACKEND` hardcoded to the console backend, so no email had ever actually been sent to a real inbox — just printed to the runserver log. Same "scaffolding first, keys later" pattern as Razorpay/Google OAuth/S3 storage (Features 12/16/19): build the real SMTP wiring now, real credentials added by the user once they have an account (Gmail App Password, SendGrid, etc.).

## What was built

**`rental_project/settings.py`** — `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`/`EMAIL_USE_TLS`/`DEFAULT_FROM_EMAIL` now read from `.env` (all blank/default today). A new `EMAIL_CONFIGURED = bool(EMAIL_HOST and EMAIL_HOST_USER and EMAIL_HOST_PASSWORD)` flag picks `EMAIL_BACKEND` at startup: real SMTP backend once all three are set, otherwise the same console backend as before — **zero behavior change** until real credentials are added, exactly like every other scaffolded integration on this site. Works with Gmail (via an App Password, not the account password), SendGrid, AWS SES, or any standard SMTP provider — documented directly in `.env.example` including the Gmail App Password caveat.

No code change was needed in `ForgotPasswordView` itself — it already called Django's own `send_mail` machinery under the hood, reading `EMAIL_BACKEND` from settings; it now genuinely sends once configured, for free.

**Real "Send Test Email"** (`dashboard/views.py::admin_send_test_email`, System Settings page) — not just a status label. A Super Admin can send a real test email to their own account and immediately see whether it worked (a real inbox message) or exactly why it didn't (the real SMTP exception — wrong password, host unreachable, etc. — shown back via Django messages, not swallowed). Reuses the `admin_settings` page's existing "Integration Status" card, extended with a third real row (Email (SMTP): Configured/Not Configured, alongside the existing Razorpay/Google Sign-In rows) and the send-test button.

## Files

**Backend**: `rental_project/settings.py` (EMAIL_* settings block), `dashboard/views.py` (`admin_send_test_email`, `admin_settings` extended with the 3rd integration row + `email_configured` context), `dashboard/urls.py`, `accounts/views.py` (updated a now-stale comment on `ForgotPasswordView`), `.env`/`.env.example` (+6 EMAIL_* placeholders).

**Templates**: `dashboard/templates/dashboard/admin_settings.html` (Send Test Email button + real `email_configured` check — not a hardcoded/always-true tooltip).

**Tests**: `dashboard/tests.py` — extended the existing integration-status test for the 3rd row, + 3 new (`test_send_test_email_without_smtp_configured_shows_real_error`, `test_send_test_email_is_admin_only_not_regular_admin`, `test_send_test_email_actually_sends_once_configured` — the last uses `@override_settings(EMAIL_CONFIGURED=True)` + Django's `mail.outbox`, since the test runner always forces the real network-free `locmem` backend regardless of what `EMAIL_BACKEND` resolves to, so this exercises the real `send_mail()` call path without needing actual SMTP credentials in CI).

## Verification

- `python manage.py test` — full suite passes (291 tests, up from 288).
- Manual: with `.env` still blank, System Settings correctly shows "Email (SMTP): Not Configured" / "Console (development)" and the Send Test Email button returns a clear "add credentials first" message rather than crashing or pretending to send.
- Once a user adds real Gmail/SendGrid/etc. credentials to `.env` and restarts the server: Send Test Email delivers a real message, and password-reset emails genuinely reach the user's inbox instead of only appearing in the server console.
