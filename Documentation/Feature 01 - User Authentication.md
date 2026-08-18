# Feature 01 — User Authentication

**Status:** Done and tested
**Maps to:** Workflow doc, Part 2 — Login & Registration System (public login/register/logout scoped in full; internal admin login scoped in full; mobile OTP and Google login deferred — see "What was deliberately left out" below)

## What this feature does

Before this feature, the entire site was a UI mockup: every "logged in" state in the header was a hardcoded `demo_logged_in: True` flag, and the login/register/forgot-password pages were static HTML with no real form submission. This feature replaces all of that with real, working authentication:

- **Register** (`/accounts/register/`) — creates a real account as one of three public roles (Tenant, Property Owner, Hotel/Homestay Owner), logs the user in immediately, and redirects to a role-specific dashboard.
- **Login** (`/accounts/login/`) — email + password, with the exact error message from the spec ("Invalid email or password. Please try again.") on failure.
- **Logout** — destroys the session, works from the header on every page.
- **Forgot password** (`/accounts/forgot-password/`) — email a one-time reset link, set a new password, old password stops working immediately.
- **Internal login** (`/accounts/internal-login/`) — separate login for Super Admin / Admin, with a role tab (Super Admin / Admin) that must match the account's actual role.
- **Role-based redirect** — every login/registration sends the user to the right place: `/tenant/dashboard/`, `/owner/dashboard/`, `/hotel/dashboard/`, `/admin/dashboard/`, `/super-admin/dashboard/`. A user can't open another role's dashboard (403).
- The header (every page, via `base.html`) now shows the real logged-in state: user's initials, name, and a working Log Out button — instead of the fake "Hi, Rahul" mock.

## What was built (technical summary)

- **`accounts.User`** — a custom Django user model (`accounts/models.py`) replacing Django's default `auth.User`, using **email** as the login field instead of username. Fields: `email`, `full_name`, `mobile_number`, `role` (tenant / owner / hotel / admin / super_admin), `is_email_verified`, `is_mobile_verified`, `accepted_terms`. This required resetting the local dev database (it only had empty system tables, no real data) since `AUTH_USER_MODEL` can't be changed after the first migration.
- **`accounts/forms.py`** — `RegisterForm`, `EmailLoginForm` (shared by public + internal login), `AdminLoginForm`, plus thin subclasses of Django's built-in `PasswordResetForm` / `SetPasswordForm` so the reset emails/pages match the site's styling.
- **`accounts/views.py`** — function-based views for register/login/logout/internal-login, and class-based views (subclassing `django.contrib.auth.views`) for the 4-step password reset flow (request → email sent → set new password → done).
- **`dashboard` app** — now has real `urls.py`/`views.py` with one `role_dashboard` view reused for all five roles via `path(..., {'role': 'tenant'}, name='tenant')`. Each dashboard is a placeholder page confirming who's logged in — the real dashboards (listings, inquiries, etc.) are separate future features (workflow doc Parts 7–10).
- **`accounts/context_processors.py`** — adds `user_dashboard_url` to every page's context so the header's avatar link always points to the right dashboard, from any template.
- Templates (`login.html`, `register.html`, `admin_login.html`, `forgot_password.html`, and 3 new reset templates) were converted from static mockups to real Django forms: `{% csrf_token %}`, server-rendered field values/errors, and the account-type/role-tab JS now writes into real hidden form fields instead of just toggling CSS classes.
- Added shared `.alert`/`.form-error-banner`/`.field-error` styles (`base.css`) and a `partials/messages.html` include (used by both `base.html` and `auth_base.html`) so Django's messages framework and form errors display consistently everywhere.

## What was deliberately left out (and why)

The workflow doc's Part 2 spec includes mobile OTP login, Google OAuth login, and OTP-based (not link-based) password reset. None of these were built:

- **Mobile OTP / Google login** need a real SMS gateway and Google Cloud OAuth credentials — neither exists in this project yet. Building fake versions would mean shipping buttons that don't actually work, which defeats the point of "build it, test it, it works."
- **Password reset** uses a secure emailed link (Django's standard, battle-tested token system) instead of a 6-digit OTP, for the same reason — no SMS/email-OTP provider is wired up. In dev, the reset email is printed to the `runserver` console instead of a real inbox (`EMAIL_BACKEND = console` in `settings.py`).
- **Admin account creation** — the spec says only the Super Admin can create Admin accounts, but that UI is part of the Super Admin Dashboard (Part 10), which isn't built yet. For now, an internal account is created via Django's `manage.py createsuperuser` (customized to default `role=super_admin`).

These are natural candidates for later features once a real SMS/email provider and the admin dashboards exist.

## How it was tested

**Automated** — `accounts/tests.py`, 14 tests, run with `python manage.py test accounts`:
- Registration creates a user, logs them in, redirects to the correct dashboard; rejects duplicate emails and mismatched passwords; owner/hotel roles redirect correctly.
- Login accepts correct credentials and redirects correctly; rejects wrong passwords with the spec's exact error message.
- Dashboards require login (redirect to `/accounts/login/?next=...`) and enforce role ownership (403 on cross-role access).
- Logout actually ends the session.
- Internal login: Super Admin logs in and redirects correctly; a public-role account is rejected; a real admin account is rejected if the wrong role tab is selected.
- Forgot password: full flow — request → emailed link → set new password → old password stops working, new one works; a reset link can't be reused after the password has actually been changed (Django's token is derived from the password hash, so it self-invalidates).

**Manual** — verified via `curl` against the running dev server: form fields render with the right ids/classes so existing password-toggle and account-type JS still works, the header shows real initials/name/logout when logged in and Login/Register when logged out, and the account-type cards on `/accounts/register/` correctly reflect the selected role.

### Try it yourself

Test accounts created during testing (still in the local dev DB):

| Role | Email | Password |
|---|---|---|
| Tenant | `tenant@example.com` | `NewStrongPass456` |
| Property Owner | `owner@example.com` | `StrongPass123` |
| Hotel/Homestay Owner | `hotel@example.com` | `StrongPass123` |
| Super Admin | `admin@example.com` | `AdminPass123` (log in at `/accounts/internal-login/`) |

## Files touched

`accounts/models.py`, `accounts/managers` (in models.py), `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py`, `accounts/admin.py`, `accounts/context_processors.py`, `accounts/tests.py`, `accounts/templates/accounts/*.html` (all), `accounts/templates/accounts/emails/*.txt` (new), `dashboard/views.py`, `dashboard/urls.py`, `dashboard/templates/dashboard/stub.html` (new), `templates/partials/header.html`, `templates/partials/messages.html` (new), `templates/partials/icon.html` (added `logout` icon), `templates/base.html`, `templates/auth_base.html`, `static/css/base.css`, `static/css/auth.css`, `static/css/pages.css`, `static/js/auth.js`, `rental_project/settings.py`, `rental_project/urls.py`, `core/views.py`, `hotels/views.py`, `properties/views.py`, `roommates/views.py` (removed the `demo_logged_in` mock from these four).

## What's next

With real accounts in place, the natural next features are the ones that need a logged-in user: **Property Listing System** (owner posts a property) or fleshing out the **Tenant/Owner Dashboards** — to be decided before starting the next feature, per the one-feature-at-a-time process.
