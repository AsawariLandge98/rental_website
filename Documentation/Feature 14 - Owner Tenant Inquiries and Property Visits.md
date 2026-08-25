# Feature 14 — Owner Tenant Inquiries & Property Visits Management

**Status:** Done and tested
**Maps to:** Owner dashboard sidebar — "Tenant Inquiries" and "Property Visits" (present in the original owner dashboard screenshot batch from Feature 05, left as "Coming Soon" stubs at the time)

## What this feature does

Feature 05 shipped the Owner dashboard with these two nav items already screenshotted and linked, but stubbed as "Coming Soon" since the underlying `inquiries`/`visits` apps didn't exist yet. Both apps were built since (Feature 03, tenant-facing; Feature 08, admin-facing), and the `Visit` model's own docstring already said *"the owner sees it land in their own dashboard once that's built."* This closes that loop — same page shape as the Feature 08 admin versions, scoped to the logged-in owner's own properties instead of the whole platform.

- **Tenant Inquiries** (`/owner/dashboard/inquiries/`, replaces the stub) — every inquiry sent about the owner's own listings, with real stats (Total / Open / Closed), search by tenant or property, status filter, and a Close/Reopen action.
- **Property Visits** (`/owner/dashboard/visits/`, replaces the stub) — every visit scheduled on the owner's own listings, with real stats (Total / Scheduled / Completed / Cancelled), the same search/filter, and a Cancel action (notifies the tenant, same as the admin-side cancel).
- Both views are hard-scoped with `property__owner=request.user` at the queryset level, and the POST actions additionally use `get_object_or_404(..., property__owner=request.user)` — an owner can never see or act on another owner's inquiries/visits, not even by guessing a URL.

## Deliberate scope

The original screenshots for these pages (shown much earlier, as part of the tenant-side "My Inquiries"/"My Visits" mockups reused for this nav slot) showed stat cards for "Responded / Awaiting Response" and "No Show" — states that don't exist on the real models. `Inquiry` only has Open/Closed (no in-app messaging exists to track a "response" — contact happens directly via the phone/email/WhatsApp already shown on the listing, per the low-friction-contact precedent from Feature 03), and `Visit` only has Scheduled/Completed/Cancelled (no no-show tracking). Rather than invent fake states to match the mockup pixel-for-pixel, the stats shown are the real ones — same honesty call as Features 07/09/12.

No in-app owner-to-tenant messaging was added — replying stays out-of-band (phone/WhatsApp/email), consistent with how contact already works everywhere else on the platform.

## How it was tested

**Automated** — new `OwnerInquiriesVisitsTests` in `dashboard/tests.py` (7 tests): access is owner/hotel-only (403 for tenant), stats and search/filter scope correctly to the owner's own properties, Close/Reopen round-trips an inquiry, Cancel actually cancels a visit and notifies the tenant, and — the important one — an owner **cannot** close another owner's inquiry or cancel another owner's visit (`404`, not silently ignored). Also renamed a stale test (`test_coming_soon_sections_reachable_for_owner_and_blocked_for_tenant` → `test_owner_routes_reachable_for_owner_and_blocked_for_tenant`) since these two routes are no longer stubs — same drift pattern already seen and fixed in Feature 13. Full suite: 180 tests passing.

**Manual** — no browser automation tool was available this session, so verification was done directly against the dev database via Django's test client: confirmed both pages render with the real seed owner's genuine zero-inquiry state (empty-state message, not an error), then against `smoke_owner@example.com` (an existing test account with 3 real inquiries and 2 real visits from earlier feature testing) confirmed accurate stat counts and real property/tenant rows rendered, exercised the Close and Cancel actions end-to-end (verified the DB state changed and the tenant notification was created), then reverted that account's data back to its original state since this was a mechanical check, not a walkthrough worth keeping a record of.

### Try it yourself

Log in as any owner or hotel account — Tenant Inquiries and Property Visits in the sidebar are now real pages scoped to that account's own listings.

## Files touched

`dashboard/views.py` (+`owner_inquiries`, `owner_inquiry_set_status`, `owner_visits`, `owner_visit_cancel`; removed `inquiries`/`visits` from `OWNER_COMING_SOON_SECTIONS`), `dashboard/urls.py` (real routes replacing the `owner_coming_soon` stub routes), `dashboard/templates/dashboard/owner_inquiries.html`, `owner_visits.html` (new), `dashboard/tests.py` (+`OwnerInquiriesVisitsTests`; renamed one stale test).

## What's next

Remaining gaps across the whole project: Roommate/Hotel detail pages, decorative search filter checkboxes, and Reviews — none of which have a prior screenshot on file in this conversation to build against pixel-for-pixel.
