# Feature 18 — General & SEO Settings

## Context

The user shared a large generic "System Settings" mockup (General/User/Property/Payment/Email/Notification/Security/Branding/SEO/Backup/API-Keys tabs) and initially asked to replicate it wholesale. Researched first: almost none of it maps to anything real in this codebase — no commission/GST math anywhere (zero-brokerage + flat Razorpay subscription is the actual model), no SMTP account, no 2FA package installed, no branding-color system (colors are fixed CSS variables), no backup tooling, and none of Google Maps/Firebase/reCAPTCHA/OpenAI are integrated anywhere.

Given the explicit choice to build real functionality rather than fake toggles, the scope was broken into phases and the user picked **General + SEO** to start. This feature is that phase.

## What was built

**Extended `cms.SiteSettings`** (the singleton from Feature 17) rather than creating parallel models — General and SEO are both "site-wide settings," same real source of truth:
- **General/branding**: `platform_name` (default `'Rentora'`), `logo`, `favicon` — real image uploads, wired into `header.html`/`footer.html` (falls back to the existing hardcoded SVG mark + "Rentora" text when unset) and a real `<link rel="icon">` tag in all three base templates (`base.html`, `auth_base.html`, `dashboard/_base.html`) when a favicon is uploaded.
- **SEO**: `google_analytics_id`, `facebook_pixel_id`, `og_image` — real tracking scripts (gtag.js / Meta Pixel) only render in `<head>` when their ID is actually set; never fabricated, same "real when set, absent otherwise" pattern as Feature 17's social links.

**New `cms.PageSEO` model** — one row per real public page (`home`/`about`/`contact`/`become_host`/`terms`/`privacy`, fixed choices like `LegalPage`), with `meta_title`/`meta_description`. Seeded via data migration with real per-page copy. Each of the 5 relevant `core/views.py` views (`home`, `about`, `contact`, `become_host`, `legal_page`) now passes `page_seo` in context; each page's `{% block title %}` uses the DB value if set, else falls back to its existing hardcoded default, and a new `{% block meta_description %}` renders a real `<meta name="description">` tag when set.

**Real `sitemap.xml`** via Django's built-in `django.contrib.sitemaps` (added to `INSTALLED_APPS`) — `core/sitemaps.py` defines `StaticViewSitemap` (the 7 real public routes) and `PropertySitemap` (every currently-`PUBLISHED` `Property`, with real `lastmod` from `updated_at`). Mounted at `/sitemap.xml`. Uses Django's `Sites` framework for the domain (`SITE_ID=1`) — defaults to `example.com`; needs a one-time real-domain update via Django admin → Sites when deployed (not something this feature fakes a value for).

## Admin CRUD

- **Site Settings** (`/admin/dashboard/cms/site-settings/`) — extended with a new "General" section (Platform Name, Logo, Favicon) above the existing Contact/Social sections. Now takes `enctype="multipart/form-data"` for the file uploads.
- **SEO Settings** (`/admin/dashboard/cms/seo/`, new) — sitewide Analytics/Pixel/OG-image form, plus a real list+edit for all 6 `PageSEO` rows (no add/delete — fixed page choices, mirrors `LegalPage`'s pattern). Every save logs to `AuditLog` via `log_admin_action`, consistent with every other CMS admin action.
- CMS hub (`/admin/dashboard/cms/`) now has 5 quick-link cards (added "SEO Settings"); `.help-cards` converted from a fixed `repeat(4,1fr)` grid to `auto-fit`/`minmax(200px,1fr)` so a 5th card doesn't orphan onto its own row — consistent with the "auto-fit any device" pattern used sitewide this session.

## Files

**Backend**: `cms/models.py` (+7 fields on `SiteSettings`, +`PageSEO` model), `cms/forms.py` (+`SeoSettingsForm`, +`PageSEOForm`, `SiteSettingsForm` extended), `cms/migrations/0008…0010` (schema + seed), `dashboard/views.py` (+`admin_seo_settings`, +`admin_page_seo_form`, `admin_site_settings` now handles `request.FILES`), `dashboard/urls.py`, `dashboard/context_processors.py` (`PAGE_TITLES`), `core/views.py` (`_page_seo()` helper, wired into 5 views), `core/sitemaps.py` (new), `rental_project/settings.py` (+`django.contrib.sitemaps`), `rental_project/urls.py` (+`/sitemap.xml`).

**Templates**: `dashboard/templates/dashboard/admin_seo_settings.html`, `admin_page_seo_form.html` (new); `admin_site_settings.html`, `admin_cms_faqs.html`, `_sidebar_admin.html` (edited); `templates/base.html`, `auth_base.html`, `dashboard/templates/dashboard/_base.html` (favicon + meta_description block + conditional Analytics/Pixel scripts); `templates/partials/header.html`, `footer.html` (logo/platform-name swap, dynamic copyright); `core/templates/core/home.html`, `about.html`, `contact.html`, `become_host.html`, `legal_page.html` (dynamic title + meta description blocks).

**CSS**: `static/css/base.css` (`.brand__logo`), `static/css/dashboard.css` (`.help-cards` → auto-fit).

**Tests**: `cms/tests.py` (+`PageSEOSeedTests`, platform-name default check), `core/tests.py` (+`SitemapTests`, `PageSeoRenderingTests`, platform-name/Analytics-script rendering checks), `dashboard/tests.py` (+`AdminSeoSettingsTests`, extended `AdminCmsSiteSettingsTests`), `properties/tests.py` unaffected by this feature (Feature 17 already covered the photo-limit real-setting tests this builds alongside).

## Deliberately not built (still fake/unbuilt for this site)

Everything else from the original mockup — Commission %/GST (conflicts with the zero-brokerage model), SMTP config, 2FA, IP whitelist, real DB backup/restore, dynamic branding *colors* (only logo/favicon are real — the color system stays fixed CSS variables), and any Google Maps/Firebase/reCAPTCHA/OpenAI key fields (none integrated anywhere). These remain explicitly out of scope until/unless their underlying feature is built for real.

## Verification

- `python manage.py test` — full suite passes (263 tests) after this feature, including 216 in the directly-touched apps (`cms`, `core`, `dashboard`, `properties`).
- Manual: `/sitemap.xml` returns real static pages + published properties only (drafts excluded); Home's `<meta name="description">` renders from the seeded `PageSEO` row; Analytics/Pixel scripts are absent by default and appear only once an ID is saved; header/footer brand mark and copyright reflect a changed Platform Name; uploading a favicon makes `<link rel="icon">` appear across public, auth, and dashboard pages.
