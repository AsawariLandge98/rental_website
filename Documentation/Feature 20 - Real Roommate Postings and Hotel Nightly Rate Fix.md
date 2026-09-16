# Feature 20 — Real Roommate Postings + Hotel Nightly Rate Fix

## Context

From the "what important features are still missing" review, the user confirmed: make Roommates and Hotels real. Researched both first:

- **Hotels** turned out to already be real (browsing/detail wired to actual `Property` rows in an earlier pass this session) — just two concrete bugs: nightly rate was collected by the wizard but never displayed anywhere (every hotel card/detail page silently showed `monthly_rent` labeled "/month"), and the budget filter matched against `monthly_rent` while its own label said "per night."
- **Roommates** was still 100% fake — no model at all, a hardcoded 8-entry Python list, and every card ended in a disabled "Profile Coming Soon" button. Confirmed via research that it couldn't cleanly reuse `Property`: the fake UI already promises two structurally different postings — "Looking for a Roommate" (a person with an existing, unlisted flat) vs "Offering a Room" (a real vacancy) — not one property listing. Scope confirmed via AskUserQuestion: support both posting types; contact info shown directly on the detail page, same no-gating pattern as property owner contact.

## What was built

**Hotels (`properties/views.py`, `hotels/views.py`)** — `_property_card_context()` now picks `nightly_rate` + `"night"` as the price/period for any `Property` where `is_bookable` (category in HOTEL_CATEGORIES), else `monthly_rent` + `"month"` as before. Since this one shared function feeds property cards, the detail page, and similar-properties everywhere on the site, the fix applies uniformly with three small template edits (`property_card.html`, `property_detail.html` x2) swapping a hardcoded `/month` for `/{{ property.price_period }}`. `hotels/views.py`'s budget filter now filters on `nightly_rate` instead of `monthly_rent`.

**Roommates — new `RoommatePosting` model** (`roommates/models.py`), standalone, not FK'd to `Property`:
- `poster` (User FK), `posting_type` (Looking/Offering), `photo` (optional, 2MB cap via the existing `MaxFileSizeValidator`)
- `room_type`, `city`, `area_locality`, `monthly_rent`
- `gender_preference` (Male/Female/Any), `occupation` (Student/Working Professional/Any), `roommates_needed`, `move_in_date`, `description`
- `is_active` (poster can mark a posting filled/inactive — hides it from search without deleting it)
- Real, derived (never stored/fabricated) `badge_label`/`badge_color` — "Looking for N" for Looking posts, "Available Now" / "Available from <date>" for Offering posts, computed from real fields.
- Real `poster_age`, computed from the poster's own `User.date_of_birth` if they've set one — simply absent from the card when they haven't, same honesty rule used everywhere else (never a fabricated age).

**Real CRUD + contact** (`roommates/views.py`, `forms.py`, `urls.py`): list (real filters — posting type, gender preference, budget, city/locality search — same shape as the old fake filters, now querying the DB), detail (real page replacing "Coming Soon", with the exact same Call/WhatsApp/Email contact-sheet pattern as property owner contact — a local `_poster_contact_options()`/`_phone_digits()` rather than importing from `properties` to keep the apps decoupled), create/edit (login required), toggle-active, delete (poster-only, enforced via `get_object_or_404(..., poster=request.user)` — an IDOR check, matching the pattern the security audit confirmed elsewhere on the site). Any logged-in user (any role) can post — no owner/tenant restriction, since offering a room or looking for one isn't role-specific in real life.

**Templates**: `roommates/templates/roommates/list.html` rewritten (real queryset, cards now real links instead of a disabled button, sidebar CTA goes to the real create flow instead of plain registration); `detail.html` and `form.html` new, reusing `properties.css`'s `.detail-layout`/`.detail-card`/`.owner-card`/`.wizard-grid`/contact-sheet classes for visual consistency with the property detail page rather than inventing a parallel design language.

## Files

**Backend**: `roommates/models.py`, `forms.py` (new), `views.py`, `urls.py`, `admin.py`, `migrations/0001_initial.py`; `properties/views.py` (`_property_card_context` nightly-rate fix); `hotels/views.py` (budget filter fix).

**Templates**: `roommates/templates/roommates/list.html` (rewritten), `detail.html`, `form.html` (new); `templates/partials/property_card.html`, `properties/templates/properties/property_detail.html` (price-period fix).

**CSS**: `static/css/roommates.css` (`.roommate-card` made link-safe, `--empty` states, new detail/form page classes; removed the now-dead `.roommate-card .btn.is-disabled` rule).

**Tests**: `roommates/tests.py` (19 new — list filters, detail rendering, contact options, IDOR checks on edit/delete, real age derivation), `hotels/tests.py` (3 new — nightly rate display, monthly rate unaffected for residential, budget filter matches the right field).

## Verification

- `python manage.py test` — full suite passes (288 tests, up from 266).
- Manual: a hotel-category listing now shows its real nightly rate with "/night"; a residential listing is unaffected ("/month" as before); the hotels budget filter now actually matches nightly rate. Roommate list page shows real posted listings with working detail links; posting create/edit/delete is scoped to the actual poster; contact sheet shows real Call/WhatsApp/Email using the poster's own account details.
