# Feature 23 — Reviews & Ratings

## Context

Last item off the "important, not yet built" list from this batch. Deliberately built *after* Feature 22 (Visit Completed tracking) rather than before it — a review system with no real gate on who can post is exactly the kind of fake trust signal this site has repeatedly removed elsewhere (fake "Verified" badges in Feature 02/04, the fake testimonials list removed in Feature 17). Filled in the `reviews` app, which had sat as an empty registered stub since the start (`reviews/models.py` was still the Django-generated `# Create your models here.`).

## What was built

**`reviews.Review`** — `tenant` (FK), `property` (FK), `rating` (1-5), `comment` (optional, 1000 chars), timestamps. A real `UniqueConstraint` on `(tenant, property)` — one review per tenant per property; resubmitting updates it rather than creating a duplicate.

**The real gate**: `reviews/views.py::submit_review` only accepts a review if `Visit.objects.filter(tenant=..., property=..., status=Visit.Status.COMPLETED).exists()` — the exact signal Feature 22 just made real. No completed visit, no review; a clear error message explains why instead of silently failing.

**Inline on the property detail page** (`properties/views.py::property_detail`, `property_detail.html`) — a real "Reviews & Ratings" section:
- Real aggregate (`Avg('rating')` + count) shown as a rating badge next to the section heading — genuinely absent (not zeroed-out) when there are no reviews yet, "No reviews yet" instead.
- The real review list — reviewer name, star rating, comment, relative timestamp (`timesince`, matching the sitewide convention).
- A pure-CSS interactive star-picker (radio inputs + `flex-direction: row-reverse` + `~` sibling selectors — no JS) for submitting: shows "Write a Review" for an eligible tenant with none yet, "Edit Your Review" pre-filled if they already have one, or a plain note explaining they need a completed visit first. Nothing shown at all for owners/guests/other roles — no dead UI for people who could never use it.

**Real admin moderation** (`/admin/dashboard/reviews/`, new sidebar item) — mirrors the established FAQ/Support-Ticket admin pattern: stats (total, average rating), search (tenant/property/comment text), rating filter, Delete (audit-logged via the existing `log_admin_action`). No edit — a review's own author edits it by resubmitting on the property page; admin's only real lever is removal for abuse/spam.

**Deliberately scoped out this pass**: no rating badge on property *cards* (search results/home/hotels grids) — would need query-level `annotate()` across every list view to avoid an N+1 query problem, a real follow-up, not bundled in here. No owner-reply-to-review. No review editing/deleting by the tenant themselves beyond resubmitting (no explicit delete button) — a small, defensible gap, not a blocker.

## Files

**Backend**: `reviews/models.py`, `forms.py` (new), `views.py`, `urls.py`, `admin.py` (new/filled-in), `migrations/0001_initial.py`; `properties/views.py` (`property_detail` context: `reviews`, `review_average`, `review_count`, `user_review`, `can_review`); `dashboard/views.py` (`admin_reviews`, `admin_review_delete`), `dashboard/urls.py`, `dashboard/context_processors.py`; `rental_project/urls.py` (mounted `reviews.urls` at `tenant/dashboard/reviews/`).

**Templates**: `properties/templates/properties/property_detail.html` (new Reviews & Ratings section — the exact spot a fake one lived and was removed from, earlier this session); `dashboard/templates/dashboard/admin_reviews.html` (new), `_sidebar_admin.html` (new nav item).

**CSS**: `static/css/properties.css` (`.review-summary-*`, `.review-list`/`.review-item*`, `.review-form`, `.star-rating` — the CSS-only star picker).

**Tests**: `reviews/tests.py` (new — the completed-visit gate, resubmission updates instead of duplicating, the DB uniqueness constraint, invalid rating rejected, owner blocked from submitting), `properties/tests.py` (+`PropertyReviewsDisplayTests` — honest empty state, real review/average rendering, the write-form only appearing after a completed visit), `dashboard/tests.py` (+`AdminReviewsTests` — access control, stats, search, rating filter, delete + audit log).

## Verification

- `python manage.py test` — full suite passes (313 tests, up from 297).
- Manual: a tenant with no completed visit sees "Complete a visit... to leave a review" and gets a real error if they try anyway; after Feature 22's "Mark Completed" action, the same tenant sees a real star-picker form; submitting shows up immediately in the real review list and updates the aggregate; resubmitting edits the same review instead of adding a second one; Admin → Reviews shows it platform-wide and Delete removes it with a real audit-log entry.
