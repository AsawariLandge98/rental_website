# Feature 07 — Admin Properties (Platform-Wide Moderation)

**Status:** Done and tested
**Maps to:** Workflow doc, Part 9 — Admin Dashboard / Part 11 — Verification & Approval (partial)

## What this feature does

The user shared 11 more Super Admin screenshots (System Settings, Notifications Management, Audit Logs, Reports & Analytics, Subscription Plans, Payments & Transactions, Inquiries Management, Properties + Verification, Admin Roles/Permissions) and asked to "make this super admin dashboard." Scoped down via `AskUserQuestion` to **Properties + Verification only** — several other pieces (Audit Logs, Payments, Subscriptions billing, granular Admin RBAC) need entirely new models this feature doesn't build.

A second, more consequential question was asked before any code was written: the screenshots show an Approve/Reject/"Pending Approval" workflow that reads like a pre-publish gate, but Feature 02 explicitly decided "no verification needed to post property" and owners have been publishing instantly ever since. Confirmed: **keep publishing instant — Approve/Reject is real post-publish moderation, not a queue that blocks new listings.**

- **Admin Properties** (`/admin/dashboard/properties/`) — real platform-wide list: stat cards (Total / Active / Pending Review / Rejected / Draft), search (title/city/owner name/owner email) + status + verification + property-type filters, a real data table, pagination.
- **Property detail** (`/admin/dashboard/properties/<id>/`) — full listing info, owner info, a real **Listing Completeness** checklist, and moderation actions.
- **Approve** — sets `Property.verified_at`/`verified_by` (real admin bookkeeping, timestamped and attributed), notifies the owner.
- **Reject** (`/admin/dashboard/properties/<id>/reject/`) — requires a reason, pulls the listing back to Draft (already hidden from search — no new status value needed), notifies the owner with the reason, and shows a reason banner on the owner's own My Properties row until they fix and republish (which auto-clears it).
- **Pause / Resume / Archive** — the admin equivalent of the owner's own self-service actions, but with no ownership restriction (an admin can moderate any owner's listing); Archive additionally notifies the owner since it's an admin actively taking their listing down.

## What "Approve / Reject" means under no-gate moderation

Three new `Property` fields carry real meaning without reversing Feature 02:
- `verified_at` + `verified_by` — set by Approve. Shown only inside the admin panel as internal bookkeeping ("an admin looked at this and signed off") — **not** a new public-facing "Verified" badge. The public badge (`Property.badge`) still only reflects the paid listing plan, per the Feature 02/04 precedent against fake verification claims.
- `rejection_reason` — set by Reject, cleared automatically the moment the owner successfully republishes (`properties/manage_views.py::publish_listing` / `set_listing_status`).

Stat buckets derive honestly from these — **Pending Review** = published, never verified, not rejected; **Rejected** = has a rejection reason; **Verified** = has a `verified_at`. No fake "Reported"/"Suspended"/"Expired" buckets from the screenshots — those aren't real concepts here (no tenant-reporting feature, no listing-expiry feature).

## Scope trims (flagged, not silently dropped)

- **No admin Edit** — admin moderates status, doesn't edit listing content. Editing stays owner-only via the existing wizard.
- **No admin Delete** this round — the most destructive, least-needed action here; owners can already delete their own listings.
- **No fake document-upload "Verification Checklist."** The screenshots show checkboxes like "Owner Identity Proof," "NOC/Society Approval," "Legal Verification" — none of that data exists anywhere in this codebase. The detail page shows a real **Listing Completeness** checklist instead, reusing `Property.REQUIRED_FOR_PUBLISH`/`missing_publish_requirements()` — the actual, already-enforced publish-readiness logic from Feature 02. Every line on it is backed by a real stored field, both the done (green check) and missing (red x) states.

## How it was tested

**Automated** — 112 tests total across the project (`python manage.py test`), including a new `AdminPropertiesTests` class in `dashboard/tests.py` and two new tests in `properties/tests.py`:
- Admin reaches the list and detail pages; tenant/owner get 403.
- Stats are correct.
- Search and status filters work.
- Approve sets `verified_at`/`verified_by` and notifies the owner.
- Reject without a reason re-shows the form instead of saving; with a reason it flips the listing to Draft, records the reason, clears verification, and notifies the owner.
- Admin can Archive a property owned by a different user entirely (no ownership check, unlike the owner's own equivalent view), and the owner is notified.
- Republishing a previously-rejected listing clears the rejection reason (`properties/tests.py`).
- My Properties renders the rejection banner when a reason is set.

**Manual** — ran the dev server, drove it with Playwright as `admin@example.com`: browsed Properties, opened a real listing's detail page, walked through the full Reject flow (form → reason → redirect → updated stats/pills), and confirmed no console errors at 1440px and 390px widths. This caught one real UI bug: the Listing Completeness checklist used a checkmark icon for *every* line regardless of pass/fail, which read as "everything failed but has a checkmark" — fixed to show a red X for missing items and a green check for done ones. **Note on manual testing:** the sample "Untitled draft" listing used for the reject-flow walkthrough belongs to the developer's own real account (`owner@gmail.com`, not a seeded test account) — the rejection reason and the notification it generated were both cleaned up afterward via the Django shell so no test artifacts were left on real user data.

### Try it yourself

Log in as `admin@example.com` / `AdminPass123` (Super Admin), go to Properties in the sidebar.

## Files touched

`properties/models.py` (+`verified_at`, `verified_by`, `rejection_reason`, `verification_state` property), `properties/migrations/0004_property_verification_fields.py` (new), `properties/manage_views.py` (`publish_listing`/`set_listing_status` clear `rejection_reason` on republish), `properties/templates/properties/manage/my_listings.html` (rejection banner row), `properties/tests.py` (2 new tests). `dashboard/views.py` (removed the `properties` stub section; added `admin_properties`, `admin_property_detail`, `admin_property_approve`, `admin_property_reject`, `admin_property_set_status`), `dashboard/urls.py` (real routes replacing the stub), `dashboard/tests.py` (`AdminPropertiesTests`), `dashboard/templates/dashboard/admin_properties.html`, `admin_property_detail.html`, `admin_property_reject.html` (new). `static/css/properties.css` (verification status-pill variants, `.publish-checklist li.is-done` modifier).

## What's next

Inquiries, Property Visits, Payments, Subscription Plans, Reports & Analytics, Support Tickets, and CMS Management are all still "Coming Soon" stubs. Admin Roles & Permissions (the granular RBAC deferred again this round) and Audit Logs remain the two biggest structural pieces not yet started — both need new models and would touch every existing admin view.
