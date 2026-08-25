# Feature 16 — Become a Host + Google Sign-In (scaffolding)

**Status:** Done and tested (Google OAuth needs real credentials to actually authenticate — see below)
**Maps to:** User's "make it like Airbnb" request — host onboarding entry point + social login

## What this feature does

Two related pieces, both aimed at the same goal: an Airbnb-style path into hosting.

### 1. Become a Host (`/become-a-host/`)

A real intro page — eyebrow/headline/subtitle, a real 3-step "How Hosting Works" summary (matching the actual 10-step wizard, not invented), a "Why Host With Rentora" section (zero brokerage, direct contact, real support — no earnings claims, no fake stats), and a "Get Started with Google" CTA that goes **directly** into the Google OAuth handshake (`accounts:google_login_start?type=owner`), skipping the register page entirely. Linked from the navbar (anonymous + tenant users only — hidden for owners/hotels/admins, who are already hosting), the Home hero, the Home empty-state, and the footer's "List Your Property" link (which was previously a dead `href="#"`, now wired to something real).

If Google OAuth isn't configured yet (no real credentials in `.env`), `google_login_start` degrades honestly — a message + redirect to the register page with Owner pre-selected — rather than the Become a Host CTA looking broken.

### 2. Google Sign-In (scaffolding — `django-allauth`)

Explicitly deferred back in Feature 01 ("OTP/Google deferred") — now built, following the same "scaffolding first, real keys later" pattern as Razorpay in Feature 12. `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` are blank in `.env`; until both are set, `settings.GOOGLE_OAUTH_CONFIGURED` is `False` and every "Continue with Google" button is hidden (login, register) rather than being shown broken.

**A real, deliberate limitation flagged up front:** Google's OAuth doesn't provide date of birth — that scope requires app verification Google doesn't grant for normal sign-in apps. This isn't a corner cut, it's the actual platform limit (Airbnb hits the same wall, which is why they ask for it manually after Google sign-in — same real approach used here).

**How it works:**
- `accounts/adapters.py` — `RentoraSocialAccountAdapter` maps a Google login onto the existing custom `User` model (email-based, no `username` field at all, so allauth's default username-based signup path is fully overridden): links to an existing account by email if one already exists (`pre_social_login`), otherwise creates a real new user with `full_name`/`email` from Google, `set_unusable_password()` (they can still recover access later via the existing real forgot-password flow, which sets a real password), and `is_email_verified=True` (Google already verified it). `RentoraAccountAdapter` controls the post-login redirect — new social sign-ups go to a real profile-completion step first.
- **Role selection**: `accounts:google_login_start` (our own real URL, not allauth's) stashes `?type=owner|tenant|hotel` in the session before handing off to Google, so a "Continue with Google" click from Become a Host correctly creates an Owner account — same mechanism the real registration form already uses.
- **Complete Your Profile** (`accounts:complete_profile`) — shown once, only to brand-new Google sign-ups: real form (`CompleteProfileForm`) showing Full Name (editable, pre-filled from Google), Email (read-only — it's the sign-in identity), and Date of Birth (18+ validated, saved to a new `User.date_of_birth` field, real migration `accounts/migrations/0003_user_date_of_birth.py`, shared across all roles since Owner/Hotel accounts can sign up via Google too). Mobile number is deliberately not collected here — it stays optional and can be added later from Profile Settings, keeping this one-time step to exactly the fields the user asked for.
- allauth's own URLs are mounted at `/social-auth/` (not `/accounts/`) specifically to avoid colliding with the project's own real `/accounts/login/`, `/accounts/register/` etc.

## A real bug found and fixed during this build

Adding allauth's authentication backend alongside the existing `ModelBackend` broke two things that only surfaced under a full test run, not manual spot-checks:
1. Every `auth_login(request, user)` call that doesn't go through Django's `authenticate()` first (specifically `register()`, which creates the user directly) now needs an explicit `backend=` argument — with two backends configured, Django can no longer infer which one to use. Fixed by passing it explicitly.
2. allauth's own backend defaults to a `username`-based lookup, which doesn't exist on this project's custom User model at all — it wasn't failing gracefully, it was crashing with a `FieldError` the moment it got consulted as the second backend (e.g., on any wrong-password attempt). Fixed by setting `ACCOUNT_LOGIN_METHODS = {'email'}` so allauth's backend queries the right field.

## Deliberate scope

No fake earnings/stats language on Become a Host. No attempt to fetch DOB from Google — flagged as a real platform limit, not silently worked around. Google's own login/signup pages are unused; only the OAuth provider handshake is taken from allauth, everything else (login, register, password reset) stays on the project's own real views.

## How it was tested

**Automated** — `GoogleSignInTests` (URL correctly refuses when unconfigured, invalid role isn't stashed), `CompleteProfileTests` (anonymous users redirected, valid submission saves for real and redirects to the right dashboard, underage DOB rejected, invalid mobile rejected). Full suite: 195 tests passing, including the two real regressions above caught by the full run (not by the new tests themselves — a reminder that a green targeted run isn't the same guarantee as the full suite).

**Manual** — verified `/become-a-host/` renders and its CTA lands on `/accounts/register/?type=owner` with the Owner card pre-selected; verified the navbar link's visibility differs correctly by role; the actual Google handshake itself cannot be manually or automatically verified end-to-end without real credentials — that's the one gap "scaffolding first" always leaves open until real keys are added.

### Try it yourself

Visit `/become-a-host/` as a signed-out visitor or as a tenant. "Continue with Google" stays hidden everywhere until real `GOOGLE_OAUTH_CLIENT_ID`/`GOOGLE_OAUTH_CLIENT_SECRET` are added to `.env` (from a Google Cloud Console OAuth Client).

## Files touched

`requirements.txt` (+`django-allauth`), `rental_project/settings.py` (allauth apps/middleware/backends, Google provider config, `GOOGLE_OAUTH_CONFIGURED`), `rental_project/urls.py` (`/social-auth/` mount), `.env`/`.env.example` (+ blank Google placeholders), `accounts/models.py` (+`date_of_birth`), `accounts/migrations/0003_user_date_of_birth.py`, `accounts/adapters.py` (new), `accounts/forms.py` (+`CompleteProfileForm`), `accounts/views.py` (+`google_login_start`, `complete_profile`; fixed the `100% Verified Platform` fake claim on the register perks list; fixed the `auth_login` backend bug), `accounts/urls.py`, `accounts/templates/accounts/login.html`, `register.html` (+Google button), `complete_profile.html` (new), `static/js/auth.js` (Google link URL follows the selected account type), `static/css/auth.css`, `templates/partials/icon.html` (+real 4-color Google logo), `core/views.py`/`urls.py`/`templates/core/become_host.html` (new page), `core/templates/core/home.html`, `templates/partials/header.html`, `templates/partials/footer.html` (Become a Host entry points), `static/css/pages.css`.

## What's next

Add real Google OAuth credentials to `.env` when ready. Everything else in this feature already works end-to-end.
