# Feature 02 — Property Listing System

**Status:** Done and tested
**Maps to:** Workflow doc, Part 4 — Property Listing System, Steps 1–9, 11–14 (Step 10, Owner Verification, is explicitly removed per instruction — see below)

## What this feature does

Property Owners and Hotel/Homestay Owners can now create **real** property listings through a guided, multi-step wizard that follows the workflow doc's structure step-by-step — and those listings are what Search Results and the Property Detail page actually show. Before this feature, both of those pages displayed 8 hardcoded fake properties from a Python dict; now they query the real database, and anyone can list a property and see it appear.

The wizard, in order:
1. **Select Listing Category** — Residential, Room, PG, Shared, Hotel, Guest House, Homestay
2. **Property Information** — title, description, type, furnishing, age, areas, floor, bed/bath/balcony count, parking
3. **Location** — state/district/city/area/landmark/pincode/full address (full address is never shown publicly)
4. **Tenant Preferences** — family / bachelor / students / professionals / anyone (multi-select)
5. **Rent Details** — monthly rent, deposit, maintenance, electricity, water, brokerage
6. **Availability** — available-from date, minimum stay, move-in date, lease duration
7. **Amenities** — grouped checkboxes (Basic / Home / Society), seeded from the doc's exact list
8. **Photos & Media** — real file upload, 5 minimum to publish, 25 maximum, set-cover and delete
9. **Contact Preferences** — Chat / Call / WhatsApp / Email (multi-select)
10. **Preview** — shows the listing exactly as the public will see it, lists anything still missing, lets you pick a **Listing Plan** (Free/Silver/Gold/Premium — stored for real, no payment gateway yet)
11. **Publish** — validates everything, sets the listing live immediately

A draft is created the moment you pick a category (step 1), and every step after that saves to the real database as you go — so "save as draft and continue later" genuinely works: close the browser at any point and your progress is still there in **My Listings** (`/properties/manage/`).

**My Listings** (linked from the Owner/Hotel dashboard) shows every listing you've created with its real status, and lets you edit, preview, publish, pause, resume, archive, or delete each one.

## The "no verification needed" change

The workflow doc's Step 10 (Owner Verification: mobile OTP, email verification, government ID upload) and the "Pending Verification" / "Pending Review" stages of the property status flow are **not implemented** — a listing goes straight from Draft to Published the moment the owner clicks Publish, no approval step. This was an explicit instruction for this feature, not a scope-trimming decision I made unilaterally like the OTP/Google deferral in Feature 01.

Because of that, I also went further and **removed every "Verified Property" / "Verified" badge and the "Showing verified and active properties only" claim** from the search results page, property cards, and the property detail page — those were hardcoded UI in the original mockup and would now be actively false. The `badge` shown on a listing (Featured / Premium) is derived only from the real, stored Listing Plan chosen in the wizard — never from a verification claim.

The `Property.Status` field still includes `pending_verification` and `pending_review` choices in the database schema (unused by any code path right now) so that a future Admin Dashboard feature (workflow doc Parts 9/11) can add the approval workflow back in later without a schema migration.

## What was deliberately scoped down (and why)

- **One form per step, not a session-based form wizard framework.** Each step is its own Django view + `ModelForm` that saves directly to the real `Property` row created at step 1 — genuinely real, genuinely resumable, but simpler than a formtools-style wizard.
- **Google Maps location picker** — needs a Google Maps API key (same category of external dependency as Google login in Feature 01). Skipped; latitude/longitude fields weren't added to the model at all rather than shipping a fake map.
- **Listing Plans (Free/Silver/Gold/Premium)** are stored for real and drive the Featured/Premium badge, but there's no payment gateway — every plan is free to select right now. Real enforcement is Subscriptions (Part 12), a separate future feature.
- **Advanced search filtering** (the sidebar's Bedrooms/Furnishing checkboxes) is still decorative, same as before this feature. The top search bar (City, Area, Property Type, Budget) is now fully real and queries the database — full sidebar filtering is explicitly the next roadmap item, Property Search & Discovery (Part 5), not this one.
- **Reviews & ratings, "Prime Location" nearby-landmarks** on the detail page are separate future features (Part 14, and a maps/places integration); the detail page now shows honest empty states (sections hide themselves) instead of the old fake review data.

## How it was tested

**Automated** — `properties/tests.py`, 19 tests, run with `python manage.py test properties` (33 total across the whole project, all passing):
- Model logic: `missing_publish_requirements()` correctly lists every gap (including "needs 5 photos"); `can_publish` flips to true once complete; the `badge` property reflects listing plan, never verification; cover photo falls back sensibly.
- Full wizard flow: create → fill all 8 steps with real data → upload 5 real photos → publish, asserting the DB state after every single step.
- Publish is blocked with a clear reason list when incomplete; the 25-photo cap is enforced server-side even if someone bypasses the UI.
- Access control: anonymous users are redirected to login; a Tenant account gets 403 on `/properties/manage/`; an owner gets 404 trying to edit another owner's listing (not 403 — doesn't even reveal it exists).
- My Listings shows only the logged-in owner's own properties.
- Status transitions (publish → pause → resume → archive) work, and "resume to published" is correctly blocked if the listing no longer meets the publish requirements.
- Public visibility: only `published` listings appear in Search Results or are reachable at their detail URL — draft/paused/archived all 404 on the detail page and are absent from search.
- Search filtering by city, property type, and budget range all work against real data.
- Explicit regression test that no "Verified Property" text ever renders on a listing page.

**Manual** — walked through the live flow via the running dev server as the `owner@example.com` test account: created a draft, filled in Property Information, confirmed the Preview page's missing-requirements checklist matched what was actually missing, and confirmed the search page renders with zero remaining references to "verification"/"verified properties."

### Try it yourself

Log in as `owner@example.com` / `StrongPass123` (or `hotel@example.com` / `StrongPass123`), then from the header avatar menu go to your dashboard → **Manage My Listings** → **Add New Listing**. Fill in the 8 steps (photos need 5 real image files to be able to publish), then Preview → Publish. Your listing then appears on `/properties/` and at its own detail page for anyone, logged in or not.

## Files touched

`properties/models.py` (new: `Property`, `PropertyPhoto`, `Amenity`), `properties/migrations/0001_initial.py`, `properties/migrations/0002_seed_amenities.py` (new), `properties/admin.py`, `properties/forms.py` (new), `properties/manage_views.py` (new), `properties/views.py` (rewritten — real queries replace the hardcoded `PROPERTIES` dict), `properties/urls.py`, `properties/tests.py`, `properties/templates/properties/manage/*.html` (new: `_wizard_head`, `step_category`, `step_generic`, `step_choices`, `step_amenities`, `step_photos`, `preview`, `my_listings`), `properties/templates/properties/property_detail.html`, `properties/templates/properties/search_results.html`, `templates/partials/property_card.html`, `templates/partials/icon.html` (added `sofa`, `table`, `tv`, `dumbbell`, `pool`, `playground`, `garden`), `dashboard/templates/dashboard/stub.html`, `core/templatetags/core_extras.py` (added `is_radio`/`is_textarea` filters), `static/css/base.css` (relocated the step-indicator styles so both Accounts and Properties can use them), `static/css/properties.css` (wizard, option-cards, photo grid, listing cards), `rental_project/settings.py` (added `django.contrib.postgres` for the tenant/contact-preference array fields).

## What's next

Per the roadmap, natural next steps are **Property Search & Discovery** (wire up the still-decorative sidebar filters against this real data) or **Roommate/Hotel listing flows** for the `roommates`/`hotels` apps, which still show hardcoded dummy data the same way `properties` did before this feature. To be decided before starting.

## Update — Direct owner contact, no inquiry gating (2026-08-14)

The original build (above) kept the property detail page's "Contact details will be shared once your inquiry is approved by the owner" copy from the original mockup, since there was no real inquiry-approval system to back that promise. Per explicit instruction, that gating is removed: **contact details are visible immediately, with no inquiry step required.**

What changed:
- **Real Call / WhatsApp / Email links.** `properties/views.py` now builds real `tel:`, `https://wa.me/`, and `mailto:` links from the owner's actual `mobile_number`/`email` (already collected at registration in Feature 01). A 10-digit number is assumed to be Indian and gets a `+91` prefix for `tel:`/`wa.me`. The WhatsApp link comes pre-filled with a message naming the property.
- **Respects the owner's stated preference.** Only the channels the owner selected in the wizard's Contact Preferences step (Part 4, Step 11) are shown; if they didn't pick any, all three are offered rather than showing nothing.
- **"Contact Owner" now opens a real bottom sheet** (`.contact-sheet` in `properties.css` + `initContactSheet()` in `main.js`) instead of being a dead `href="#"` link — tapping Call/WhatsApp/Email in the sheet does the real thing (opens the phone dialer, opens WhatsApp with a prefilled chat, or opens the mail client). Built mobile-first: it's a slide-up sheet from the bottom of the screen on every size, matching the same pattern already used by the search page's filter drawer, rather than a desktop-style popup modal.
- The sidebar's "Preferred Contact Method" list uses the same real links directly (no popup needed there, it's already inline).
- The address-privacy note was reworded — it no longer references a non-existent inquiry-approval step; it now just says the exact address isn't public and to ask the owner directly.

4 new tests in `properties/tests.py` (`OwnerContactTests`, 23 properties tests / 37 total now) cover: real `tel:`/`wa.me`/`mailto:` hrefs render correctly, only the owner's selected channels appear, empty preferences fall back to showing all three, and the old inquiry-gating text is gone for good. Verified live against a real listing created by the project owner during testing.

**Why no inquiry system was built instead:** Inquiries (tracking who asked about what, letting an owner approve/reject before sharing contact info) is its own future roadmap item. Given the explicit instruction to make contact details visible without one, building a whole approval pipeline just to immediately bypass it made no sense — this keeps the site honest about what actually exists right now.
