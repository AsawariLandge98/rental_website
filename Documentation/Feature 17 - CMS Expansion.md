# Feature 17 — CMS Expansion

## Context

The only real CMS before this feature was `cms.FAQ` (Feature 11) — a single model with two placements (Contact page, Tenant Help & Support). Everything else on the public marketing pages was either hardcoded Python lists in `core/views.py` or dead `href="#"` links. Researched first (per the established workflow) before building, which surfaced two things worth flagging rather than quietly "CMS-ifying":

1. **Fake testimonials.** `core/views.py` had a hardcoded `TESTIMONIALS` list — 3 fake names, fake cities, `pravatar.cc` stock avatars, hardcoded 5-star ratings, no backing model. This directly contradicts the site's own repeated "no fake data" precedent (Features 02/03/04/16 all removed similar fabricated trust claims). **Removed** rather than made "CMS-editable" — a CMS shouldn't make fake content easier to keep faking.
2. **Terms & Conditions / Privacy Policy don't exist.** Registration already legally requires accepting them (`accounts/forms.py`'s `accept_terms` field), but both links were `href="#"`. This is a real compliance gap, not just a marketing-copy gap.

Everything else — Home/About/Become-a-Host's icon+title+text sections, and the sitewide support phone/email/social links — were genuine, editable-without-a-deploy candidates.

## What was built

**`cms` app — three new models**, alongside the existing `FAQ`:

- **`SiteSettings`** — single-row singleton (`support_phone`, `support_email`, `business_address`, 4 social URLs). `save()` forces `pk=1`; `SiteSettings.load()` get-or-creates it. Exposed sitewide via a new `cms.context_processors.site_settings` context processor (registered in `settings.py`), so `{{ site_settings.support_phone }}` works in any template without per-view plumbing. Replaces phone/email that were hardcoded and duplicated in both `help_support.html` and `owner_help_support.html`.
- **`LegalPage`** — `slug` (fixed choices: `terms`/`privacy`), `title`, `body`. Real page at `/legal/<slug>/` (`core/views.py::legal_page`, 404s on an unknown slug). Seeded via data migration with genuine draft copy describing what the site actually does (direct owner/tenant contact, zero brokerage, Razorpay-processed subscription payments, what account data is collected) — **not legal advice, not lawyer-reviewed**, a reasonable starting point an admin can edit.
- **`ContentBlock`** — `placement` (7 choices: `home_why_choose`, `home_how_it_works`, `about_values`, `about_why_choose`, `about_trust_steps`, `host_steps`, `host_perks`), `icon`, `title`, `text`, `order`, `is_published`. Same shape/pattern as `FAQ`. Seeded via data migration from the 7 hardcoded lists it replaced (`WHY_CHOOSE_US`, `HOW_IT_WORKS`, `ABOUT_VALUES`, `ABOUT_WHY_CHOOSE`, `HOW_TRUST_WORKS`, `BECOME_HOST_STEPS`, `BECOME_HOST_PERKS`) — migrated verbatim, same as Feature 11's FAQ seed.

`PROPERTY_TYPES` (Home's "Browse by Property Type" tiles) was deliberately **not** migrated — it's functionally tied to `Property.Category` filter links, not pure marketing copy, and converting it risks breaking real filtering if an admin edits a label out of sync with the category enum.

## Admin CRUD

Mirrors the FAQ pattern exactly (`dashboard/views.py`, all `@admin_required`, every mutation logged via `log_admin_action` → `AuditLog`):

- **Content Blocks** (`/admin/dashboard/cms/content-blocks/`) — full list/search/placement-filter/paginate + add/edit/delete/toggle-publish, same shape as FAQ management.
- **Legal Pages** (`/admin/dashboard/cms/legal-pages/`) — list + edit only (no add/delete — the two slugs are fixed by the `Slug` choices, not open-ended).
- **Site Settings** (`/admin/dashboard/cms/site-settings/`) — single edit form, no list (it's a singleton).

The existing FAQ list page (`/admin/dashboard/cms/`) is now the CMS hub — three link-cards at the top point to the new sections. Admin sidebar's "CMS Management" link highlights active across all of them.

## Public-facing wiring

- `core/views.py::home/about/become_host` now query `ContentBlock.objects.filter(placement=..., is_published=True)` instead of returning hardcoded lists — templates needed almost no changes since Django template `.` access works identically on dict keys and model attributes (only `about.html`'s plain-string `values` loop needed `{{ value }}` → `{{ value.title }}`).
- Home's "What Our Users Say" testimonials section removed entirely (template + `.testimonial-*` CSS in `home.css`).
- `templates/partials/footer.html`: Terms/Privacy links now point to the real pages; social icons only render if their URL is actually set in Site Settings (no more dead `#` icons); added a real contact line (phone/email) sourced from Site Settings, shown only if set; removed an unqualified "Verified properties...trusted" claim from the footer tagline (same "no fake trust claims" issue Features 02/03/04/16 already fixed elsewhere, just missed here).
- `accounts/templates/accounts/register.html`: Terms & Conditions / Privacy Policy checkboxes now link to the real pages.
- `dashboard/templates/dashboard/help_support.html` and `owner_help_support.html`: support phone/email cards now read from `site_settings` (conditionally shown) instead of two separately hardcoded copies of the same string.

## Files

**Backend**: `cms/models.py` (+3 models), `cms/forms.py` (+3 forms), `cms/admin.py` (Django admin registration for all 3), `cms/context_processors.py` (new), `cms/migrations/0004…0007` (schema + 3 data-seed migrations), `dashboard/views.py` (+11 admin views), `dashboard/urls.py`, `dashboard/context_processors.py` (`PAGE_TITLES`), `core/views.py` (rewritten `home`/`about`/`become_host`/+`legal_page`), `core/urls.py`, `rental_project/settings.py` (context processor registration).

**Templates**: `dashboard/templates/dashboard/admin_content_blocks.html`, `admin_content_block_form.html`, `admin_legal_pages.html`, `admin_legal_page_form.html`, `admin_site_settings.html` (new); `admin_cms_faqs.html`, `_sidebar_admin.html`, `core/templates/core/home.html`, `about.html`, `templates/partials/footer.html`, `accounts/templates/accounts/register.html`, `help_support.html`, `owner_help_support.html` (edited); `core/templates/core/legal_page.html` (new).

**CSS**: `static/css/dashboard.css` (`.help-card` made clickable-safe), `static/css/pages.css` (`.legal-page*`), `static/css/base.css` (`.footer-contact`), `static/css/home.css` (removed `.testimonial-*`, `.testimonials-grid`).

**Tests**: `cms/tests.py` (+`SiteSettingsSingletonTests`, `ContentBlockOrderingTests`, `LegalPageSeedTests`), `core/tests.py` (+`CmsContentBlockRenderingTests`, `LegalPageTests`, `SiteSettingsContextTests`, no-fake-testimonials check), `dashboard/tests.py` (+`AdminCmsContentBlockTests`, `AdminCmsLegalPageTests`, `AdminCmsSiteSettingsTests` — full CRUD + access-control + audit-log coverage, mirroring `AdminCmsFaqTests`).

## Verification

- `python manage.py test cms core dashboard` — full pass including new CRUD/access-control/audit-log/public-rendering tests.
- Manual: `/`, `/about/`, `/become-a-host/`, `/legal/terms/`, `/legal/privacy/`, `/contact/` all render real DB-backed content; `/legal/bogus/` 404s; footer Terms/Privacy links resolve to real pages; testimonials section is gone from Home.
