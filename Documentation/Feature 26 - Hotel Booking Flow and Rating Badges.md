# Feature 26 — Hotel Booking Flow and Rating Badges

## Context

Follow-up to the "what's still pending" status report (asked in Hinglish: "agr koi problems hai batao"). Two items from that report were fully buildable without any external account/credential (unlike Google/Razorpay/SMS/S3, which need the user's own action) — user said "jo pending bola hai wo sab ache se banao." Both built in this pass.

## Part 1 — Hotel Booking Flow

`bookings/models.py` (`Booking`) and the tenant-side `bookings/views.py` (`request_booking`, `my_bookings`, `cancel_booking`) already existed with real, working logic — but were completely disconnected from the rest of the app: no `bookings/urls.py`, not mounted in `rental_project/urls.py`, no owner-side confirm/decline, no templates anywhere, and no "Book Now" UI on the property detail page. A hotel/homestay guest could only send an Inquiry or request a Visit — the same flow as a regular monthly rental, which doesn't make sense for a per-night stay.

**What was completed:**
- `bookings/urls.py` (new) mounted at `tenant/dashboard/bookings/`.
- **Owner side** (`dashboard/views.py`): `owner_bookings` (list, stats, search/status filter, pagination — mirrors `owner_visits` exactly), `owner_booking_confirm`, `owner_booking_decline`. Confirming re-checks date overlap against other already-confirmed bookings for that property at confirm time (not just at request time) — two tenants can both have a PENDING request for overlapping dates, so confirming one must block confirming the other.
- **Admin side**: `admin_bookings` — platform-wide, read-only oversight (no cancel/refund action, same reasoning as Payments having none).
- **The "Book Now" UI** (`properties/property_detail.html`): for a bookable listing (`property.is_bookable` — Hotel/Guest House/Homestay), the "Schedule Visit" button is replaced with "Request to Book", opening a real slide-in sheet (reusing the existing `initSlideSheet()` JS pattern from Inquiry/Visit) with check-in/check-out date pickers, a guest count, and a live nights × nightly-rate total preview computed client-side. Regular rentals are completely unaffected — still show Schedule Visit as before.
- Sidebar nav links added for all three roles (tenant "My Bookings", owner "Bookings", admin "Bookings").

**Deliberately not built**: payment collection at booking time (Razorpay isn't configured yet — same as Subscriptions, a booking is a real request the host must confirm, not an instant paid transaction), no refund/webhook flow, no owner-side cancel of an already-confirmed booking (mirrors Visit's scope).

## Part 2 — Rating Badges on Card Grids

Explicitly deferred out of Feature 23 (Reviews) to avoid an N+1 query — every property card in a grid would otherwise need its own `Review.objects.filter(property=...).aggregate()` call. Solved with `properties/views.py::_with_rating(queryset)` — a single `.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews', distinct=True))` applied at the queryset level before card contexts are built, so a grid of 20 cards costs the same one extra query regardless of size.

Applied to all three real card grids: Search Results, Home's featured properties, and the Hotels list. The shared `partials/property_card.html` now renders a real star + average + count badge (e.g. "★ 4.3 (12)") — and, matching the site's no-fake-data convention, **renders nothing at all** for a listing with zero reviews rather than a fake "0.0" or a "No ratings" label cluttering every card in a grid.

## A note on scope not taken further

Two more items from the same status report — Google Sign-In, Razorpay, SMS OTP, cloud storage, and the production domain — were explicitly **not** touched here: all five are already fully coded (scaffolding-first pattern from Features 12/16/19/21/24) and only need real external credentials the user has to obtain themselves (a Google Cloud OAuth client, a Razorpay account, an SMS gateway account, an AWS/S3-compatible account, a real domain post-deploy). No code change would move any of them forward.

## Files

**Backend**: `bookings/urls.py` (new), `dashboard/views.py` (+`owner_bookings`, `owner_booking_confirm`, `owner_booking_decline`, `admin_bookings`), `dashboard/urls.py`, `dashboard/context_processors.py`; `properties/views.py` (`_with_rating()`, `is_bookable`/`rating`/`review_count` added to `_property_card_context()`, applied to `search_results`); `core/views.py` (home), `hotels/views.py` (hotel_list) — both now use `_with_rating()`; `rental_project/urls.py` (mounted `bookings.urls`).

**Templates**: `dashboard/templates/dashboard/my_bookings.html`, `owner_bookings.html`, `admin_bookings.html` (all new); `_sidebar_tenant.html`, `_sidebar_owner.html`, `_sidebar_admin.html` (nav links); `properties/templates/properties/property_detail.html` (booking sheet + button swap); `templates/partials/property_card.html` (rating badge).

**CSS**: `static/css/base.css` (`.status-pill--confirmed`/`--declined`, `.property-card__rating`); `static/js/main.js` (`initBookingSheet()`).

**Tests**: `bookings/tests.py` (new — request validation, overlap rules, my-bookings scoping, cancel), `dashboard/tests.py` (+`OwnerAdminBookingsTests` — access control, scoping, confirm/decline, the confirm-time overlap re-check, admin platform-wide visibility), `properties/tests.py` (+`PropertyDetailBookingUiTests`, +`RatingBadgeOnCardsTests`), `hotels/tests.py` (+`HotelRatingBadgeTests`).

## Verification

- `python manage.py check` — clean.
- `python manage.py test` (full suite) — run to confirm no regressions; see session notes for final count.
- Manual: a tenant on a homestay listing sees "Request to Book" with a working date-range sheet and live price preview; the host sees it under Bookings, Confirm/Decline both notify the tenant; a second overlapping request against an already-confirmed booking is correctly blocked on Confirm. A reviewed listing shows a real star badge on Search/Home/Hotels; an unreviewed one shows nothing.
