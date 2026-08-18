# Feature 06 — Admin Dashboard + User Management

**Status:** Done and tested
**Maps to:** Workflow doc, Part 9 — Admin Dashboard (partial)

## What this feature does

Admin and Super Admin accounts previously landed on the same generic `dashboard/stub.html` placeholder used by every internal role before Feature 05. The user shared 6 target screenshots (Settings, My Profile, main Dashboard w/ charts, Support Tickets, Properties/Listing Management, User Management) plus another giant "master prompt" describing a full React+TypeScript+DRF+JWT Admin Panel with ~17 modules and granular RBAC. Same as Feature 05: the rewrite was declined, and scope was confirmed down via `AskUserQuestion` to **Admin Dashboard + User Management only**.

- **Admin Dashboard home** (`/admin/dashboard/`, `/super-admin/dashboard/`) — one view/template serves both roles (no differentiated capability exists yet between them). Real stat cards: Total/Active/New This Month/Blocked Users (platform-wide, tenant+owner+hotel only), Total/Active Properties, Total Inquiries, Scheduled Visits, Open Support Tickets. A real Recent Activity feed merges the latest Users/Properties/Inquiries/Support Tickets by timestamp — not a fake activity log.
- **User Management** (`/admin/dashboard/users/`) — stat cards, search (name/email/phone) + role + status filters, a real data table (avatar, role, email, phone, status, joined date, real per-user property/inquiry counts via `annotate(Count(...))`), pagination, and **Block/Unblock** actions that toggle `User.is_active` — the same field the tenant's own "Delete Account" flow already uses. This has a real effect: Django's auth backend refuses login for `is_active=False` accounts, so a blocked user is actually locked out, verified end-to-end with a headless-browser session.
- **My Profile** (`/admin/dashboard/profile/`) — same reused pattern as Owner's: `AccountBasicsForm` + Django `PasswordChangeForm`.
- **Notifications** — already role-agnostic, linked from the new sidebar.
- **Full admin sidebar nav** (Dashboard, User Management, Properties, Inquiries, Property Visits, Payments, Subscription Plans, Reports & Analytics, Support Tickets, CMS Management, Notifications, My Profile, Settings, Logout) — consolidated from the (mutually inconsistent) screenshots. Every section beyond what's listed above goes to the same honest "Coming Soon" stub pattern first built in Feature 05, reusing its exact template.

## A real, pre-existing bug found and fixed

While wiring up the new nested routes under `/admin/dashboard/...`, every one of them redirected unauthenticated-looking users to `/admin/login/` instead of the app's own login page — including the *existing* `/admin/dashboard/` route, which turned out to have been silently broken since Feature 01. `rental_project/urls.py` registered `path('admin/', admin.site.urls)` **before** `path('', include('dashboard.urls'))`. Django's admin site has a catch-all view (for missing-trailing-slash redirects) wrapped in a permission check that requires Django's own `is_staff` flag — completely unrelated to this app's `role` field — so *any* request under `/admin/...` that isn't a real Django-admin URL got intercepted and redirected to Django's admin login, before it could ever reach `dashboard.urls`. This had no automated test coverage before now (Feature 05 didn't add access tests for the admin/super_admin routes), so it went unnoticed. Fixed by moving the `admin.site.urls` include to the end of `urlpatterns` — Django tries patterns in order, so the app's own `/admin/dashboard/*` routes now match first, and genuine Django-admin paths (`/admin/`, `/admin/login/`, `/admin/<app>/<model>/...`) still fall through correctly since nothing in `dashboard.urls` matches them. Verified both directions: the new admin dashboard works, and Django's own `/admin/` site (used via `accounts/admin.py`, `properties/admin.py`, etc.) still works unchanged.

## Deliberate scoping calls made (and why)

- **No charts.** The screenshots show line/donut charts; this round is stat cards + Recent Activity + Quick Actions, matching the Owner Dashboard's shape. No JS charting library is in place yet, and the underlying data (Payments, Subscriptions) that would make charts meaningful doesn't exist.
- **No User Detail page.** Table + inline Block/Unblock only, same shape as My Properties (Feature 05) rather than a dedicated `/admin/users/:id` route.
- **Block/Unblock only, no Delete.** Reuses `is_active`, the platform's existing safe-deactivation pattern.
- **User Management excludes internal-role accounts** (`role__in=User.PUBLIC_ROLES` only) — admins can't block each other or themselves from this page. Verified with a test that posting a block request against another admin's ID 404s rather than succeeding.
- **9 "Coming Soon" stubs** (Properties, Inquiries, Property Visits, Payments, Subscription Plans, Reports & Analytics, Support Tickets, CMS Management, Settings) — all honestly describe what's missing rather than showing fake data or a dead link.
- **`role_dashboard` view and `dashboard/stub.html` removed** — dead code once Admin/Super Admin moved off them (mirrors the Feature 05 cleanup of `.listing-card` CSS in the same spirit).

## How it was tested

**Automated** — 103 tests total across the project (`python manage.py test`), including new coverage in `dashboard/tests.py`:
- `AdminDashboardAccessTests` — admin and super_admin both reach their dashboards; tenant/owner get 403; anonymous redirects to login; all 9 stub sections return 200 for admin, 403 for tenant.
- `AdminDashboardStatsTests` — every stat is platform-wide and excludes the admin's own account from user counts; Recent Activity includes multiple event kinds.
- `AdminUsersTests` — admin accounts never appear in the list; search/role filters work; Block sets `is_active=False` **and the blocked user's next login attempt actually fails**; Unblock reverses it; blocking another admin's ID 404s.
- `AdminProfileTests` — profile update and password change work.

**Manual** — ran the dev server and drove it with a headless-browser (Playwright) script as `admin@example.com` (seeded in this dev DB as role `super_admin` — both `/admin/dashboard/` and `/super-admin/dashboard/` work for it, confirming the shared-view design), screenshotting the Dashboard, User Management (both desktop and mobile), a "Coming Soon" stub, and the mobile sidebar drawer, at 1440px and 390px widths. No console errors. Separately drove an actual Block → Unblock round-trip through the real UI (not just the API) and confirmed the row's status pill and action button update correctly both times.

### Try it yourself

Log in via `/accounts/internal-login/` as `admin@example.com` / `AdminPass123` (role: Super Admin — select "Super Admin" on the login form). The dashboard is reachable from the header avatar/brand link or directly at `/admin/dashboard/` or `/super-admin/dashboard/`.

## Files touched

`rental_project/urls.py` (URL ordering fix — see above). `dashboard/decorators.py` (+`admin_required`). `dashboard/views.py` (removed `role_dashboard`/`ROLE_TITLES`; added `admin_home`, `admin_users`, `admin_user_set_active`, `admin_profile`, `admin_profile_password`, `admin_coming_soon`, `ADMIN_COMING_SOON_SECTIONS`, `_month_start` helper). `dashboard/urls.py` (real admin/super_admin routes + 9 new paths). `dashboard/tests.py` (new test classes above). `dashboard/templates/dashboard/` — `_base.html`/`_topbar.html` (3-way role branch: tenant / owner+hotel / admin+super_admin), `_sidebar_admin.html`, `admin_home.html`, `admin_users.html`, `admin_profile.html` (new), `stub.html` (deleted, now dead code), `owner_coming_soon.html` (reused as-is for admin stubs).

## What's next

Properties, Inquiries, Property Visits, Payments, Subscription Plans, Reports & Analytics, Support Tickets, and CMS Management are all still "Coming Soon" stubs and are natural next features — Properties (platform-wide moderation) is probably the highest-value one, since it's the other half of what Feature 05 built for owners. Granular Admin RBAC (multiple admin sub-roles with different permissions) and Audit Logs remain explicitly deferred, as do Payments/Subscriptions (no billing models exist at all yet).
