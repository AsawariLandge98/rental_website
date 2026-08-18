# Feature 08 — Admin Inquiries & Property Visits

**Status:** Done and tested
**Maps to:** Workflow doc, Part 9 — Admin Dashboard (partial)

## What this feature does

Continuing the admin panel build from Features 06-07, this closes out the lowest-risk remaining piece from the Super Admin screenshot batch: platform-wide visibility into Inquiries and Property Visits, both of which already exist as real, working models (built in Feature 03 for the tenant side, given an owner-facing counterpart in Feature 05). No new models were needed — this is entirely admin visibility and light moderation on top of what already exists.

- **Admin Inquiries** (`/admin/dashboard/inquiries/`) — every inquiry any tenant has sent any owner, platform-wide. Stat cards (Total/Open/Closed), search (tenant/property/owner) + status filter, pagination. Admin can Close or Reopen any inquiry — useful for resolving disputes or clearing spam without needing either party to act.
- **Admin Property Visits** (`/admin/dashboard/visits/`) — every scheduled visit, platform-wide. Stat cards (Total/Scheduled/Completed/Cancelled), same search/filter/pagination shape. Admin can Cancel a scheduled visit, which **notifies the tenant** (their own scheduling decision is being overridden by an admin, so silence would be a bad user experience — matches the same "notify on consequential admin action" rule used for Property rejection/archiving in Feature 07).

## Scope notes

- **No "mark completed" action.** Nothing in the codebase marks a visit completed automatically or manually yet (Feature 03 never built that either — visits stay `Scheduled` until the tenant cancels them). Adding a real "Completed" workflow would mean inventing a rule for *when* a visit counts as done, which is a bigger decision than this slice's scope. Cancel is the only real, unambiguous admin action available today.
- **No inquiry reply/response feature.** The original master prompt's Inquiry Detail page (message thread, internal notes) needs message-level modeling this project doesn't have — `Inquiry` stores one message, not a thread. Left for a future feature if actually needed; Close/Reopen is the real, honest action available now.

## How it was tested

**Automated** — new `AdminInquiriesVisitsTests` class in `dashboard/tests.py`: access control (admin reaches both pages, tenant gets 403), stats are correct, status filter works, Close/Reopen round-trips correctly, Cancel sets the visit to cancelled and creates a real notification for the tenant.

**Manual** — ran the dev server, drove it with Playwright as `admin@example.com`, screenshotted both pages at 1440px and 390px widths against the real dev DB's existing smoke-test data (3 inquiries, 2 visits from `smoke_tenant@example.com`). No console errors, no layout issues (the flexbox filter-bar bug fixed in Feature 05 didn't recur, since this reuses the same `.dash-filter-bar` component).

### Try it yourself

Log in as `admin@example.com` / `AdminPass123` (Super Admin), then Inquiries or Property Visits in the sidebar.

## Files touched

`dashboard/views.py` (removed `inquiries`/`visits` from `ADMIN_COMING_SOON_SECTIONS`; added `admin_inquiries`, `admin_inquiry_set_status`, `admin_visits`, `admin_visit_cancel`), `dashboard/urls.py` (real routes replacing the two stubs), `dashboard/tests.py` (`AdminInquiriesVisitsTests`), `dashboard/templates/dashboard/admin_inquiries.html`, `admin_visits.html` (new — same stat-card/filter-bar/record-table/pagination shape as `admin_properties.html`/`admin_users.html`).

## What's next

Remaining stubs: Payments, Subscription Plans, Reports & Analytics, Support Tickets, CMS Management. The two biggest structural pieces still fully deferred: Admin Roles & Permissions (granular RBAC) and Audit Logs — both need new models and would touch every existing admin view once built.
