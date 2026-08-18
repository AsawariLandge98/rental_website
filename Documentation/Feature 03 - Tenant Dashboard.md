# Feature 03 — Tenant Dashboard

**Status:** Done and tested
**Maps to:** Workflow doc, Part 7 — Tenant Dashboard

## What this feature does

Tenants now get a real, fully-functional dashboard — before this feature, `/tenant/dashboard/` was a placeholder stub page that just confirmed you were logged in. It's built from the user's own Figma designs and covers 8 pages behind a shared sidebar + topbar shell:

- **Dashboard Home** (`/tenant/dashboard/`) — stat tiles (saved/inquiries/visits/notifications), Recently Viewed Properties (real session-based browsing history), Recommended For You (latest published listings, filtered by preferred city if set), Upcoming Visits, Latest Notifications, Quick Actions.
- **Saved Properties** (`/tenant/dashboard/saved/`) — the heart icon on every property card site-wide (search results, property detail, dashboard grids) is now a real save/unsave toggle, backed by a new `SavedProperty` model.
- **My Inquiries** (`/tenant/dashboard/inquiries/`) — every time a tenant opens the "Contact Owner" sheet on a property page, a real `Inquiry` record is logged; this page lists them with a Close action.
- **My Visits** (`/tenant/dashboard/visits/`) — a new "Schedule Visit" bottom sheet on the property page lets a tenant pick a date/time; this page lists scheduled visits with a Cancel action.
- **Notifications** (`/tenant/dashboard/notifications/`) — a real `Notification` model with a topbar bell badge (unread count via a new context processor), mark-read/mark-all-read.
- **My Profile** (`/tenant/dashboard/profile/`) — editable personal info + rental preferences, backed by a new `TenantProfile` model; shows real (mostly "Not Verified") mobile/email verification status instead of fake green checkmarks.
- **Settings** (`/tenant/dashboard/settings/`) — tabbed: Account Settings (read-only, links to Edit Profile), Change Password (Django's built-in flow), Notification Preferences, Privacy Settings, Language, and Delete Account.
- **Help & Support** (`/tenant/dashboard/help/`) — FAQ accordion + a real Support Ticket form (`SupportTicket` model, visible/actionable in Django admin — there's no live support backend, so this is the honest destination for a submitted ticket).
- **Search Properties** — the sidebar links straight to the existing, already-built `/properties/` search page rather than duplicating it inside the dashboard shell.

The whole shell (topbar + sidebar) is **locked**: both use `position: sticky`, so they stay on screen while the page content scrolls, matching what was asked for. Below 1024px width, the sidebar becomes a slide-in drawer opened by the topbar hamburger; every list/table view (My Inquiries, My Visits) collapses from a table into stacked cards on narrow screens instead of getting squeezed or scrolling sideways.

## Deliberate deviations from the literal Figma (and why)

These weren't silently decided — see the two `AskUserQuestion` confirmations at the start of this feature.

1. **No approval gating on Inquiries/Visits.** The Figma's "Pending → Waiting for owner → Contact shared" flow is dropped. Sending an inquiry or scheduling a visit is instant and confirmed immediately — consistent with Feature 02's "no inquiry-approval gate" decision. Inquiry/Visit status is just `Open`/`Closed` and `Scheduled`/`Completed`/`Cancelled`.
2. **Honest verification badges.** My Profile shows the *real* `is_mobile_verified`/`is_email_verified` fields already on `accounts.User` — since OTP verification is still deferred (Feature 01), these mostly show "Not Verified" rather than the Figma's permanent green checkmarks.
3. **Settings → Privacy** drops the "Show my contact details after inquiry approval" toggle (meaningless without a gate); kept "Show my profile to owners" and "Allow owners to contact me directly".
4. **Notification/SMS/Push toggles are real, persisted preferences**, but only Email is actually wired to delivery today (the project's existing console `EMAIL_BACKEND`). SMS/Push have no delivery infrastructure — same "stored for real, not yet enforced" pattern as Feature 02's Listing Plans.
5. **Delete Account deactivates** (`is_active = False` + logout) behind a typed "DELETE" confirmation, rather than hard-deleting the row — safer default, data recoverable via Django admin if needed.
6. **Search Properties reuses the existing page** instead of rebuilding it inside the dashboard chrome, to avoid duplicating a feature that's already real, tested, and responsive.
7. **A tenant can send multiple inquiries/visit requests for the same property.** No "already inquired" disabled-state was built — a minor simplification, not a bug.

## New models

- `properties.SavedProperty` — tenant ↔ property, unique together. Lives in `properties`, not `dashboard`, so `properties/views.py` can compute `is_saved` for the heart icon without a reverse app dependency.
- `inquiries.Inquiry` — tenant, property, message, status (`open`/`closed`).
- `visits.Visit` — tenant, property, `scheduled_at`, status (`scheduled`/`completed`/`cancelled`). Server-side rejects past datetimes even if the client bypasses the date picker's `min`.
- `notifications.Notification` — user, message, category, optional `url`, `is_read`. A small `notify()` helper is called by the inquiry/visit/ticket flows.
- `accounts.TenantProfile` — one-to-one with `User`; holds gender/DOB/occupation/about/profile photo, rental preferences (budget range, property type, furnishing, tenant type, move-in time), and the notification/privacy/language toggles. Created lazily (`get_or_create`) the first time a tenant hits any dashboard page.
- `dashboard.SupportTicket` — user, subject, category, description, optional attachment, status.

All new views are gated by a new `dashboard.decorators.tenant_required` (mirrors the existing `owner_or_hotel_required` pattern from Feature 02) — an owner/hotel/admin account gets a 403, not just a redirect.

## What was deliberately scoped down (and why)

- **Recommended For You** is a simple heuristic (latest published listings, optionally filtered to the tenant's preferred city) — no real recommendation engine.
- **Recently Viewed** is session-based (last 10 property IDs the tenant viewed, most-recent-first), not a persisted database table — genuinely real browsing history, just not queryable outside the current session/device.
- **Search-alert-driven notifications** ("5 new properties added in your preferred location") aren't built — that needs the Subscriptions/saved-search infrastructure (Part 12/13), not yet built.
- **Owner-side accept/reject on inquiries/visits** doesn't exist — the Owner Dashboard (Part 8) isn't built yet. Once it is, `Inquiry`/`Visit` status fields already have room to grow beyond open/closed if the user wants gating reintroduced later.

## How it was tested

**Automated** — 61 tests total across the project (`python manage.py test`), including new coverage in `dashboard/tests.py`, `inquiries/tests.py`, `visits/tests.py`, `notifications/tests.py`, and additions to `properties/tests.py`:
- `tenant_required` blocks owner/hotel accounts (403) and redirects anonymous users to login.
- Visiting the dashboard home lazily creates a `TenantProfile`.
- Save/unsave toggling persists correctly and is reflected as `is-saved` on the search results page.
- Sending an inquiry creates a real `Inquiry` + `Notification`; only a tenant can send one; a tenant can't close another tenant's inquiry (404, not 403 — doesn't reveal it exists).
- Scheduling a visit in the future succeeds; scheduling one in the past is rejected server-side; cancelling works.
- Profile update, notification/privacy preference saves, password change (and re-login with the new password), and Delete Account (wrong confirmation text is a no-op; typing "DELETE" deactivates and logs out) all work end-to-end.
- Support ticket submission creates a real row.

**Manual** — ran the dev server and drove it with a headless-browser (Playwright) script through all 8 tenant pages plus the property-detail Save/Contact/Schedule-Visit hooks, at both a 1440px desktop width and a 390px mobile width, checking for console errors and taking screenshots at each step. This caught two real bugs, both fixed:
1. The Help & Support page's FAQ accordion didn't collapse, because the dashboard shell doesn't load `properties.css` (where `.filter-group` is defined) by default — fixed by adding it to that page's `extra_css` block.
2. On narrow phones, the property detail page's sticky bottom bar clipped the "Contact Owner" button text off-screen, because its buttons had `flex-shrink: 0`. Fixed by letting the buttons share space (`flex: 1 1 auto`) with tighter padding on mobile.

Also fixed while reviewing (pre-existing, not introduced by this feature, but visible throughout the dashboard's property cards): prices were rendering as `₹18,000.00` instead of `₹18,000` everywhere (`property_card.html`, `property_detail.html`, and the owner's My Listings/Preview pages) — `DecimalField` values keep their stored decimal places through `|intcomma`. Fixed by adding `|floatformat:"0"` first.

### Try it yourself

Log in as `tenant@example.com` / `NewStrongPass456`, or register a new Tenant account. The dashboard is reachable from the header avatar or directly at `/tenant/dashboard/`.

## Files touched

New apps' worth of content in previously-empty stubs: `inquiries/{models,views,urls,admin,tests}.py`, `visits/{models,views,urls,admin,tests}.py`, `notifications/{models,views,urls,admin,tests,context_processors}.py`. `properties/models.py` (+`SavedProperty`), `properties/views.py` (+`toggle_saved`, `is_saved` plumbing, free-text `q` search filter), `properties/urls.py`, `properties/admin.py`, `properties/tests.py`, `properties/templates/properties/property_detail.html` (save/inquire/schedule-visit hooks, price formatting), `properties/templates/properties/manage/{preview,my_listings}.html` (price formatting), `static/css/properties.css` (mobile bottom-bar fix). `accounts/models.py` (+`TenantProfile`), `accounts/admin.py`. `dashboard/{models,forms,decorators,views,urls,admin,tests}.py`, `dashboard/templates/dashboard/{_base,_topbar,_sidebar,home,saved_properties,my_inquiries,my_visits,notifications,profile,settings,help_support}.html` (new). `templates/partials/property_card.html` (real save-toggle wiring, price formatting). `static/css/dashboard.css` (new), `static/js/dashboard.js` (new), `static/js/main.js` (real `initSaveToggle()`, `initVisitSheet()`, inquiry-logging on contact-sheet open, `getCsrfToken()`). `rental_project/settings.py` (registered `notifications.context_processors.unread_notifications`), `rental_project/urls.py` (mounted `inquiries`/`visits`/`notifications` URLs under `/tenant/dashboard/`).

## What's next

Per the roadmap, Owner Dashboard (Part 8) is next in the workflow doc's order — it would give inquiries/visits a second side (an owner seeing and responding to what tenants have sent), and is a natural place to revisit whether any gating should be reintroduced. Admin and Super Admin Dashboards (Parts 9–10) remain after that.
