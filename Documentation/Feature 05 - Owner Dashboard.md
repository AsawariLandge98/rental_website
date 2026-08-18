# Feature 05 — Owner Dashboard

**Status:** Done and tested
**Maps to:** Workflow doc, Part 8 — Owner Dashboard

## What this feature does

Owner and Hotel/Homestay Owner accounts now get a real dashboard instead of the generic placeholder stub. The user shared a set of target screenshots (Owner Dashboard, My Properties, a 14-step Add Property wizard, Subscription Plan, Tenant Inquiries, My Visits) plus a large "master prompt" asking for a full React + Django REST Framework rewrite; both were explicitly declined in favor of staying on the existing Django templates + session-auth architecture that Features 01–04 are built on, and this feature was scoped down to just the Owner Dashboard + My Properties pages, styled to match the screenshots.

- **Owner Dashboard home** (`/owner/dashboard/`, `/hotel/dashboard/`) — 5 real stat cards (Total Listings, Active Listings, Draft Listings, Total Inquiries, Scheduled Visits), Recent Properties, Recent Inquiries, Upcoming Visits, Quick Actions. One view/template serves both the Owner and Hotel/Homestay Owner roles, since `owner_or_hotel_required` already treats them identically everywhere else (the listing wizard, My Properties).
- **My Properties** (`/properties/manage/`) — upgrade of the existing listing-management page, not a duplicate: 5 stat cards (Total / Active / Draft / Paused / Archived+Rented), a search box (title/city/locality) + status + property-type filters, a real data table (thumbnail, type, location, price, status pill, real inquiry count via `annotate(Count('inquiries'))`, actions), and pagination. Now rendered inside the dashboard shell instead of the public site chrome.
- **My Profile** (`/owner/dashboard/profile/`) — name, mobile number, read-only email, change password — reusing the same `AccountBasicsForm` and Django `PasswordChangeForm` the tenant side already uses.
- **Notifications** — the `notifications` app was already role-agnostic; just linked from the new sidebar/topbar, no new code.
- The **owner sidebar matches the full screenshot nav** (11 items) per explicit user request ("i want same nav"), not just the two pages built this round. The 5 items with no real feature yet — Tenant Inquiries, Property Visits, Subscription Plan, Settings, Help & Support — go to a shared, honest "Coming Soon" stub page rather than a dead link or fake data, the same pattern already used for the Roommate/Hotel detail pages in Feature 04.

## Deliberate calls made (and why)

1. **No "Total Views" stat.** `Property` has no view-tracking field or model. Rather than fabricate a number, it's omitted — consistent with Features 02/04's "no fake claims" precedent.
2. **No "Pending Approval" stat.** There's no admin-approval workflow yet (`Property.Status` already reserves `PENDING_VERIFICATION`/`PENDING_REVIEW` for a future Admin Dashboard feature; nothing sets them today). Replaced with a real **Draft** count instead.
3. **Owner and Hotel share one dashboard.** Building two near-identical dashboards for two roles that already share 100% of the listing-management code path would just be duplication.
4. **5 "Coming Soon" stub pages** (`dashboard:owner_inquiries`, `owner_visits`, `owner_subscription`, `owner_settings`, `owner_help`) share one view (`owner_coming_soon`) and one template, parametrized by a small `OWNER_COMING_SOON_SECTIONS` dict of (title, honest description) in `dashboard/views.py`.
5. **`owner_or_hotel_required` moved to `dashboard/decorators.py`.** It previously lived in `properties/manage_views.py`; moved to sit next to `tenant_required` (the existing convention — `properties/views.py` already imports `tenant_required` from `dashboard.decorators`) so `dashboard/views.py` didn't need a decorator defined in a different app.
6. **"Property ID" shown in the table (e.g. `PRP0003`) is the real database primary key**, zero-padded for display — not a fabricated ID scheme.

## What was deliberately scoped down (and why)

- **Tenant Inquiries / Property Visits (owner-side management)** — reading and responding to inquiries, confirming/rescheduling visits — isn't built. The dashboard's Recent Inquiries/Upcoming Visits widgets show real data read-only; the sidebar items for the full management pages are honest stubs.
- **Subscription Plan** — no real plan model beyond the `Property.listing_plan` field that already existed from Feature 02 (stored, not enforced/paid). The screenshot's pricing/plan-comparison UI wasn't built.
- **Settings and Help & Support (owner-side)** — the tenant equivalents are fairly tenant-specific (rental preferences, tenant FAQ copy); building owner-appropriate versions is left for a later pass rather than reusing content that doesn't fit.

## How it was tested

**Automated** — 88 tests total across the project (`python manage.py test`), including new coverage in `dashboard/tests.py`:
- `OwnerDashboardAccessTests` — owner reaches `/owner/dashboard/`, hotel owner reaches `/hotel/dashboard/`, tenant gets 403, anonymous redirects to login; all 5 "Coming Soon" sections return 200 for an owner and 403 for a tenant.
- `OwnerDashboardStatsTests` — stat counts (listings/inquiries/visits) reflect only the logged-in owner's own data, not another owner's; Recent Inquiries/Upcoming Visits show the real rows.
- `MyPropertiesTests` — an owner only ever sees their own properties; search-by-title, status filter, and the per-property annotated inquiry count all work; stat cards aren't affected by the active filters (they always reflect the full set).
- `OwnerProfileTests` — profile update persists; password change works and the new password logs in.

**Manual** — ran the dev server and drove it with a headless-browser (Playwright) script as `owner@example.com`, logging in and screenshotting the Dashboard, My Properties (both empty and populated with sample listings), a "Coming Soon" stub, and My Profile, at both 1440px desktop and 390px mobile widths, plus exercising the mobile sidebar drawer. No console errors. This caught one real bug: the My Properties filter bar's search box used `flex: 1 1 240px`, sized for a row layout — on mobile, where `.dash-filter-bar` switches to `flex-direction: column`, that same `240px` basis applied to *height* instead of width, rendering a ~240px-tall empty-looking search box. Fixed with `flex-basis: auto` in the mobile media query.

Also cleaned up as dead code while in this area: the old `.listing-card*` CSS rules in `properties.css` (My Properties no longer uses card rows, it uses the shared `.record-table` component already built for My Inquiries/My Visits), and the `dashboard/stub.html` template's now-unreachable owner/hotel branch (that role_dashboard route is only ever hit by Admin/Super Admin now).

### Try it yourself

Log in as `owner@example.com` / `StrongPass123` or `hotel@example.com` / `StrongPass123`. The dashboard is reachable from the header avatar/brand link or directly at `/owner/dashboard/` (`/hotel/dashboard/` for a hotel account).

## Files touched

`dashboard/decorators.py` (+`owner_or_hotel_required`, moved from `properties/manage_views.py`), `dashboard/views.py` (+`owner_home`, `owner_profile`, `owner_profile_password`, `owner_coming_soon`, `OWNER_COMING_SOON_SECTIONS`), `dashboard/urls.py` (real owner/hotel dashboard routes replacing the stub registrations, + profile/password/5 stub-section routes), `dashboard/tests.py` (new test classes above), `dashboard/templates/dashboard/` — `_base.html` (role-based sidebar include), `_topbar.html` (role-aware brand + account-menu links), `_sidebar_tenant.html` (moved from `_sidebar.html`), `_sidebar_owner.html` (new, full 11-item nav), `owner_home.html`, `owner_profile.html`, `owner_coming_soon.html` (new), `stub.html` (dead branch removed). `properties/manage_views.py` (`my_listings` — stats, search/filter, pagination, annotated inquiry counts; decorator import moved). `properties/templates/properties/manage/my_listings.html` (rewritten — dashboard shell, stat cards, filter bar, data table, pagination). `static/css/dashboard.css` (`.dash-stats` made `auto-fit` to handle both 4- and 5-card layouts, `.record-property__thumb-placeholder`, `.dash-filter-bar*`). `static/css/properties.css` (removed dead `.listing-card*` rules). `accounts/views.py` (stale comment fix on `ROLE_DASHBOARD_URL_NAME`).

## What's next

Admin and Super Admin Dashboards (Parts 9–10) remain unbuilt. The 5 "Coming Soon" stub sections (Tenant Inquiries, Property Visits, Subscription Plan, Settings, Help & Support) are natural next features once prioritized — Tenant Inquiries/Property Visits in particular would give the tenant-side Inquiry/Visit flows (Feature 03) their owner-facing counterpart. The Add Property wizard and a Tenant Dashboard craft/restyle pass are still queued from Feature 04's UI/UX plan.
