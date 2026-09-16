# Feature 19 — Security Hardening

## Context

User asked directly: "how do we secure the site so no one can hack it." Ran a code-grounded audit first (not a generic checklist) covering Django settings, auth flow, file uploads, XSS/SQLi/CSRF, IDOR, secrets, and dependencies. Findings were ranked Critical → Low and presented before building anything, per the established "research → confirm → build" workflow. The user approved the full list, specified property photos must cap at 30KB exactly (aware it's small — a deliberate storage-saving choice, not a mistake), and asked for cloud file storage.

## What was built

**1. File upload validation (Critical fix)** — `core/validators.py`: new `MaxFileSizeValidator` (deconstructible, so it serializes into migrations correctly). Applied:
- `SupportTicket.attachment` (`dashboard/models.py`) — previously accepted **any file, any size** (a real arbitrary-upload hole). Now: `FileExtensionValidator` allowlist (pdf/jpg/jpeg/png/webp/doc/docx/txt) + 5 MB cap.
- `PropertyPhoto.image` (`properties/models.py`) — 30 KB cap, per explicit instruction.
- `TenantProfile.profile_photo` (`accounts/models.py`) — 2 MB cap.
- `SiteSettings.logo` / `og_image` (`cms/models.py`) — 2 MB cap; `favicon` — 512 KB cap.

**2. Login brute-force lockout (High fix)** — `accounts/forms.py`'s `EmailLoginForm.clean()` (shared by both the public login and admin/`AdminLoginForm`, since the latter calls `super().clean()`): tracks failed attempts per request IP via Django's cache framework, locks out after 5 failures for 15 minutes, clears the counter on a successful login. Uses the default `LocMemCache` (no `CACHES` override existed) — correct for the current single-process setup; documented in-code that a real multi-worker deployment would need a shared backend (Redis/Memcached) for the lockout to apply across workers, a one-line settings change with no code change needed later.

**3. Production security headers (Critical fix)** — `rental_project/settings.py`, gated on `not DEBUG` so local dev (plain HTTP) is unaffected: `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`, `SECURE_BROWSER_XSS_FILTER`, `X_FRAME_OPTIONS='DENY'`, full HSTS (1 year + subdomains + preload). `CSRF_COOKIE_HTTPONLY` deliberately **not** set — `static/js/main.js`'s `getCsrfToken()` reads the `csrftoken` cookie directly for its `fetch()` calls (Save toggle, etc.); HttpOnly would silently break that. Documented in-code rather than silently adding a setting that breaks a real feature.

**4. `SECRET_KEY`/`DEBUG` insecure-fallback hardening (Medium fix)** — `DEBUG` now defaults to `False` (fails closed) instead of `True` — a deployment that forgets to set `DJANGO_DEBUG` no longer silently leaks stack traces. `.env` already explicitly sets `DJANGO_DEBUG=True`, so local dev is unaffected. `SECRET_KEY`'s insecure dev fallback now only applies when `DEBUG=True`; a `DEBUG=False` deployment missing `DJANGO_SECRET_KEY` raises `ImproperlyConfigured` at startup instead of silently running on the key that's visible in source.

**5. Cloud file storage (S3-compatible)** — `django-storages` + `boto3` added (`requirements.txt`). Same "scaffolding first, keys later" pattern as Razorpay/Google OAuth: `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_STORAGE_BUCKET_NAME`/`AWS_S3_REGION_NAME`/`AWS_S3_ENDPOINT_URL` read from `.env` (all blank today). With no credentials set, `STORAGES` is left untouched and Django keeps saving to local disk (`MEDIA_ROOT`) exactly as before — zero behavior change until real credentials are added. `AWS_S3_ENDPOINT_URL` makes this work with any S3-compatible provider (DigitalOcean Spaces, Backblaze B2, Cloudflare R2), not just AWS.

## Files

**Backend**: `core/validators.py` (new), `rental_project/settings.py` (DEBUG/SECRET_KEY, security headers block, S3 storage block, `+django.contrib.sitemaps`→ already there, `+storages` in `INSTALLED_APPS`), `accounts/forms.py` (login lockout), `properties/models.py`, `dashboard/models.py`, `accounts/models.py`, `cms/models.py` (validators on upload fields), migrations: `properties/0006`, `dashboard/0004`, `accounts/0005`, `cms/0011`. `requirements.txt` (+7 packages), `.env`/`.env.example` (+5 AWS_* placeholders).

**Tests**: `accounts/tests.py` — new `LoginRateLimitTests` (locks out after 5 failures, resets on success, applies to admin login too via the shared cache key) + `cache.clear()` added to `LoginLogoutTests`/`InternalLoginTests` `setUp()` (the lockout's cache state is process-global across the whole test run, not reset per-TestCase, so pre-existing wrong-password tests could otherwise accumulate toward the same threshold).

## Deliberately not built yet (from the original audit, still pending)

- `/admin/` (Django admin) — currently protected only by `is_staff`, no extra hardening added this pass.
- Image size caps beyond the fields listed above weren't asked for.

## External security (advisory — needs the user's own account/service signup, can't be done from code)

- **Cloudflare (free tier)** — real DDoS/WAF protection, hides the origin server IP, forces HTTPS at the edge.
- **A real SSL certificate** (Let's Encrypt, or the hosting provider's own) — required for `SECURE_SSL_REDIRECT`/HSTS above to mean anything in production.
- **GitHub Dependabot** (free, if the repo is pushed to GitHub) — automated alerts when a dependency (Django, allauth, boto3, etc.) gets a real CVE.
- **reCAPTCHA/hCaptcha** on login/register/contact forms — genuine bot-protection use case; scaffoldable the same "keys later" way as Razorpay if wanted later.
- **Real automated database backups** — flagged already in Feature 18's notes as a separate, bigger feature (running `pg_dump` safely from a web app needs care — not a quick add).

## Verification

- `python manage.py test` — full suite passes (266 tests) after every change, including new lockout-specific tests.
- `python manage.py check` — clean after every settings.py change (DEBUG/SECRET_KEY reordering, new `INSTALLED_APPS` entry, conditional `STORAGES`).
- Manual: uploading an oversized/wrong-extension support-ticket attachment is rejected with a real error message; 5 wrong login attempts (either login form) locks out the 6th even with the correct password; local dev is confirmed unaffected by the `DEBUG`-gated security headers and the unconfigured S3 storage block.
