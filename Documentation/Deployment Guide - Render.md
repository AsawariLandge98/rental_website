# Deployment Guide — Render

## Context

User asked for a full pre-launch audit ("check all website is there anything important missing... now we will host this"). A code-grounded sweep (Explore agent + manual checks: `manage.py check --deploy`, grepping for hardcoded URLs/stubs/placeholder content, checking `requirements.txt`/`settings.py` for production readiness) found 9 real blockers — the app worked correctly in local dev, but had never been prepared to actually run anywhere else. Confirmed host: **Render**.

This is infrastructure/deployment prep, not a numbered feature — no new user-facing behavior, so it isn't `Documentation/Feature NN`.

## What was found and fixed

1. **No production server** — `requirements.txt` had no `gunicorn`. Added `gunicorn==26.2.0`.
2. **Static files would 404 in production** — no WhiteNoise. Added `whitenoise==6.12.0`, inserted `WhiteNoiseMiddleware` right after `SecurityMiddleware` (per WhiteNoise's own ordering requirement), and set `STORAGES['staticfiles']` to `whitenoise.storage.CompressedManifestStaticFilesStorage` unconditionally (independent of whether S3 is configured for media — static assets always serve locally via WhiteNoise, only user-uploaded media moves to S3).
3. **No custom error pages** — added `templates/404.html`, `500.html`, `403.html`. Deliberately standalone (no `{% extends %}`, no context-processor dependency) since a 500 could mean the DB itself is down — Django's default error views pick these up automatically by filename convention, no `handler404`/`handler500` needed in `urls.py`.
4. **`CSRF_TRUSTED_ORIGINS` unset** — added, defaulting to `https://*.onrender.com` (works out of the box on Render's own subdomain), overridable via `DJANGO_CSRF_TRUSTED_ORIGINS` once a real custom domain exists.
5. **`SECURE_PROXY_SSL_HEADER` unset** — would have caused an infinite redirect loop on Render (which terminates TLS at a proxy and forwards `X-Forwarded-Proto`) the moment `SECURE_SSL_REDIRECT=True` kicks in under `DEBUG=False`. Now set unconditionally (harmless locally — `runserver` never sends this header).
6. **Zero production error visibility** — added a `LOGGING` dict (console handler always; `AdminEmailHandler` for `django.request` errors when `DJANGO_ADMINS` is set) plus `ADMINS`/`SERVER_EMAIL` settings, both env-driven and optional.
7. **DB config didn't support Render's `DATABASE_URL`** — Render's managed Postgres hands the app one connection-string env var, not discrete host/user/password vars. Added `dj-database-url==3.1.2`; `DATABASE_URL` is parsed when present, otherwise falls back to the original `DB_*` vars exactly as before — **local dev is completely unaffected**.
8. **Placeholder support email was live** — `support@rentora.local` (seeded in Feature 17, `.local` isn't deliverable) was rendered as a real `mailto:` link in the footer. New data migration `cms/0012_fix_placeholder_support_email.py` swaps it for the real, already-in-use Gmail account (`rentora600@gmail.com`, the same address Feature 21's SMTP already sends from) — only touches the row if it still has the exact placeholder value, so an admin who already edited it via CMS Settings is left alone. **Should be replaced with a real business support address once you have one** — editable anytime via Admin → CMS → Site Settings.
9. **`robots.txt` didn't exist** — added (`core/views.py::robots_txt`, mounted at `rental_project/urls.py`'s root alongside `sitemap.xml`), referencing the real sitemap URL and disallowing internal dashboard/admin/account-management paths from being crawled.

**`ALLOWED_HOSTS`** now also auto-appends Render's `RENDER_EXTERNAL_HOSTNAME` (a var Render sets automatically) so the default `*.onrender.com` URL works with zero manual config.

**New deploy files**: `render.yaml` (Render Blueprint — web service + free Postgres, build command runs `collectstatic`+`migrate`, all the scaffolded-but-unconfigured integrations listed as blank env vars you fill in later), `Procfile` (fallback/portable to other hosts), `.python-version` (pinned to `3.12.3` — a safely-supported version, since this machine's local `3.14.7` may not yet be available on Render's Python runtime images).

## Deliberately NOT fixed here (need a real decision from you first)

- **Media persistence**: property/profile photos still save to local disk (`MEDIA_ROOT`) until you add real `AWS_*` credentials (S3 or S3-compatible, scaffolded since Feature 19). Render's disks are ephemeral on redeploy — **uploaded photos will be lost on every redeploy until S3 is turned on.** Turn this on before your first real users upload anything.
- **`Site` row domain**: still `127.0.0.1:8000` (Feature 21) — update it to your real `*.onrender.com` URL (or custom domain) via Django admin (`/admin/sites/site/1/`) once you know your final URL, or `sitemap.xml`/password-reset emails will link to the wrong place.
- **`DJANGO_SECRET_KEY`**: `render.yaml` uses `generateValue: true` so Render generates a real random one automatically — nothing for you to do, just don't override it with the local dev placeholder.
- **Rotate the shared admin password**: `ADMIN_CREDENTIALS.md` documents `Rentora@123` for the local dev DB's admin accounts — if production starts from a fresh `migrate` (recommended) this doesn't carry over; if you ever copy the local DB to production, change these passwords first.

## Files

`requirements.txt` (+gunicorn, whitenoise, dj-database-url), `rental_project/settings.py` (WhiteNoise middleware, `STORAGES`, `DATABASE_URL` parsing, `RENDER_EXTERNAL_HOSTNAME`, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`, `LOGGING`/`ADMINS`/`SERVER_EMAIL`), `.env.example` (+documented new vars), `render.yaml` (new), `Procfile` (new), `.python-version` (new), `templates/404.html`/`500.html`/`403.html` (new), `templates/robots.txt` (new), `core/views.py` (`robots_txt`), `rental_project/urls.py` (+robots.txt route), `cms/migrations/0012_fix_placeholder_support_email.py` (new).

## Verification

- `python manage.py check` — clean.
- `python manage.py check --deploy` with `DJANGO_DEBUG=False` — only remaining warning is the test secret key being short (expected; Render generates a real one).
- `python manage.py collectstatic --noinput` with WhiteNoise's manifest storage — succeeds (143 files, 429 post-processed).
- `dj_database_url.parse()` verified against a sample `postgres://user:pass@host:5432/dbname` URL — produces the correct Django `DATABASES` dict.
- Full test suite — see session notes for final count (run in background after these changes).

## Render setup steps (for the user)

1. Push this repo to GitHub (Render deploys from a Git repo).
2. In Render: New → Blueprint → point at the repo → it reads `render.yaml` and provisions the web service + free Postgres automatically.
3. Once live, fill in whichever blank env vars you're ready for (SMTP email, Razorpay, Google OAuth, AWS S3, SMS) via the Render dashboard — each feature already degrades gracefully when its own vars are blank.
4. Update the `Site` domain (`/admin/sites/site/1/`) to your live Render URL.
5. Turn on S3 (Feature 19's scaffolding) before real users start uploading property photos, or they won't survive a redeploy.
