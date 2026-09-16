# Feature 22 — Visit "Completed" Tracking

## Context

Next off the "important, not yet built" list, chosen deliberately over Reviews & Ratings: `Visit.Status` already had a `COMPLETED` choice defined since Feature 03/08, but nothing in the codebase ever set it — flagged explicitly as a real scope boundary in Feature 08's own notes ("no 'mark completed' action added for visits since nothing in the codebase defines when a visit counts as done"). Picked this first because Reviews should only be postable against a visit/stay that genuinely happened — building that gate now means Reviews won't need to invent its own "did this really happen" logic later.

## What was built

**`dashboard/views.py::owner_visit_complete`** — new owner-side action, same shape as the existing Approve/Decline/Cancel actions (`get_object_or_404(Visit, pk=pk, property__owner=request.user)`, so an owner can only complete visits on their own properties). Two real guards, not decorative:
- Only a `SCHEDULED` visit can be completed (not pending, not already completed/cancelled).
- The visit's `scheduled_at` must have actually passed — `timezone.now() >= visit.scheduled_at` — with a clear error message if clicked early. The owner is the one physically present, so they're the natural person to confirm a visit happened (same reasoning already used for them being the Approve/Decline gate), but they still can't backdate a visit that hasn't occurred yet.

Notifies the tenant on completion, same pattern as every other visit-status-change notification.

**Tightened a related pre-existing gap** in `visits/views.py::cancel_visit` (tenant-side): it had no status guard at all — a tenant could cancel an already-`COMPLETED` visit via a direct POST, even though the UI never exposes that button for a completed visit. Now only `PENDING`/`SCHEDULED` visits are cancellable, matching what the UI already assumed. Relevant to this feature specifically: a `COMPLETED` visit needs to stay a trustworthy record (for Reviews to build on later), not something retroactively erasable.

## Files

**Backend**: `dashboard/views.py` (`owner_visit_complete`), `dashboard/urls.py`, `visits/views.py` (`cancel_visit` status guard).

**Templates**: `dashboard/templates/dashboard/owner_visits.html` (new "Mark Completed" button alongside Cancel for scheduled visits; updated page subtitle).

**Tests**: `dashboard/tests.py` (+4: complete a past-scheduled visit notifies the tenant, can't complete before the scheduled time, can't complete a pending visit, can't complete another owner's visit — plus fixed an existing test, `test_settings_page_shows_real_integration_status`, that had baked in an assumption about `.env` being unconfigured; split it into two deterministic `@override_settings`-based tests covering both the configured and unconfigured states, since it broke the moment this project's own `.env` got real Gmail SMTP credentials in the previous feature). `visits/tests.py` (+1: a completed visit can't be cancelled).

## Verification

- `python manage.py test` — full suite passes (297 tests, up from 291).
- Manual: `Visit.Status.COMPLETED` is now a real, reachable state — `owner_visits`' existing `stats.completed` count (previously always 0) now reflects real numbers once visits get marked.
