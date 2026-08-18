# Feature 09 — Admin Support Tickets & Reports and Analytics

**Status:** Done and tested
**Maps to:** Workflow doc, Part 9 — Admin Dashboard (partial) / Part 15 — Reports & Analytics (partial)

## What this feature does

Continuing straight on from Feature 08 ("ok make next pages... dont use dummy data we will make real data"), this closes out two more of the remaining "Coming Soon" stubs — both chosen specifically because they can be built with **100% real data and zero new infrastructure**, unlike Payments/Subscriptions (which need an actual billing/payment-gateway decision) or CMS/Admin-RBAC/Audit-Logs (which need new content/permission models). Those five remain deliberately deferred, not silently built with placeholder data.

- **Admin Support Tickets** (`/admin/dashboard/support/`) — every ticket any user has submitted, platform-wide (the `SupportTicket` model already existed and was already real, built in Feature 03 for tenants). Stat cards (Total/Open/Resolved), search (subject/user) + category + status filters, pagination, attachment download link where one was uploaded. Admin can Resolve or Reopen a ticket, which notifies the submitter.
- **Admin Reports & Analytics** (`/admin/dashboard/reports/`) — real, live-computed charts: New Users and Inquiries over the last 8 weeks (zero-filled weekly bar charts, Monday-aligned), Properties by Status, and Top Cities by property count. Every number comes straight from the database at request time — nothing is seeded, cached, or hardcoded.

## Deliberate calls made

- **No external charting library.** The site has zero JS dependencies today (custom inline SVG icons, no CDN scripts). Rather than pull in Chart.js/Recharts for two chart types, the weekly trends are plain CSS bar charts (`<div>` height set to a server-computed percentage) and the breakdowns are horizontal bar lists (`<div>` width set to a percentage) — both real, both accessible, no new dependency.
- **Weekly buckets are genuinely zero-filled.** A naive `TruncWeek().annotate(Count())` query only returns weeks that have at least one row, which would silently compress a mostly-quiet 8-week window into 1-2 bars. `_weekly_buckets()` in `dashboard/views.py` explicitly builds all 8 Monday-aligned week ranges first and queries each one, so a week with zero signups shows a real, honest zero bar instead of not appearing at all.
- **Property Status breakdown excludes `PENDING_VERIFICATION`/`PENDING_REVIEW`.** Those two `Property.Status` values are reserved for a future Admin verification workflow (see Feature 02's model comment) and nothing in the codebase ever sets them — showing "Pending Verification: 0" forever would be clutter, not a real data point, so they're filtered out of this specific chart (they're still valid choices everywhere else, e.g. the Feature 07 admin Properties status filter).
- **Support ticket resolution notifies the submitter but doesn't assume their role.** Tickets can technically come from any role (the model isn't tenant-only), so the notification doesn't hardcode a `/tenant/dashboard/...` URL the way early Feature 07 code did — it's sent with no deep link, since the correct destination varies by role and only tenants can actually submit tickets today anyway (owner/admin Help & Support are still their own separate stubs).

## How it was tested

**Automated** — 124 tests total across the project (`python manage.py test`), including new `AdminSupportTests` and `AdminReportsTests` classes in `dashboard/tests.py`: access control, stat correctness, category/status filtering, Resolve/Reopen round-trip with notification, and — importantly — a test that asserts the weekly user-growth chart has exactly 8 buckets with the *other 7* buckets summing to zero when all signups happened in the current week (catching exactly the zero-fill bug described above if it ever regresses), plus tests confirming the status breakdown and top-cities numbers match real created `Property` rows.

**Manual** — ran the dev server, drove it with Playwright as `admin@example.com`: the Reports page rendered live bar charts matching the real dev DB's actual signup/inquiry history (a real spike the week of 10 Aug from earlier sessions' testing, zero everywhere else) and a real Properties-by-Status/Top-Cities breakdown; the Support Tickets page correctly showed an empty state (no real tickets existed at the time) and, after creating one temporary test ticket, correctly listed and resolved it. **The temporary ticket was created against the documented `tenant@example.com` seed account and fully cleaned up (ticket + notification deleted) afterward** — after Feature 07's manual-testing slip, this was double-checked before creating it, not after.

### Try it yourself

Log in as `admin@example.com` / `AdminPass123` (Super Admin), then Support Tickets or Reports & Analytics in the sidebar.

## Files touched

`dashboard/views.py` (removed `support`/`reports` from `ADMIN_COMING_SOON_SECTIONS`; added `admin_support`, `admin_support_set_status`, `_weekly_buckets` helper, `admin_reports`), `dashboard/urls.py` (real routes replacing the two stubs), `dashboard/tests.py` (`AdminSupportTests`, `AdminReportsTests`), `dashboard/templates/dashboard/admin_support.html`, `admin_reports.html` (new). `static/css/dashboard.css` (`.mini-chart*` bar-chart component, `.bar-list*` horizontal-bar component).

## What's next

Payments, Subscription Plans, CMS Management remain stubs — Payments/Subscriptions specifically need a real decision about whether to integrate an actual payment gateway (Razorpay/Stripe test mode) versus building the data model without real billing, which is exactly the kind of consequential architecture call that should be asked about explicitly rather than assumed, the same way the Feature 07 verification-gate question was. Admin Roles & Permissions and Audit Logs remain the two biggest deferred structural pieces.
