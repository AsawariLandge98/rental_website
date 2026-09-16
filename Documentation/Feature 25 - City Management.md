# Feature 25 — City Management

## Context

User asked: "agr koi new city hai to uske liye add krna hai to new city kon add krega" (if there's a new city, who adds it?). Investigation found `properties/views.py::CITY_OPTIONS = ['Bengaluru', 'Hyderabad', 'Mumbai', 'Pune']` — a hardcoded Python list driving the city dropdown on both the Home quick-search and Search Results filter. Only a developer could add a city, since it required a code change + redeploy. Confirmed via AskUserQuestion: make it admin-manageable.

Note this was never a listing restriction — `Property.city` (and `RoommatePosting.city`) are free text, so an owner could already list in any city by typing it. `CITY_OPTIONS` only controlled what appeared as a quick-pick shortcut in the dropdown.

## What was built

**`core.City`** — `name` (unique), `order` (controls dropdown position), `is_active`. Deliberately **not** a FK target for `Property.city`/`RoommatePosting.city` — those stay free text so an owner isn't blocked from listing in a city that isn't curated yet; this model only curates the dropdown shortcut list. Seeded via data migration with the same 4 cities `CITY_OPTIONS` had (same order), so nothing changes on the surface.

**`properties/views.py::get_city_options()`** — replaces the hardcoded `CITY_OPTIONS` constant; queries `City.objects.filter(is_active=True)` ordered by `order`/`name`. Both consumers (`properties/views.py`'s own search context, `core/views.py`'s home page context, which imports this function) updated.

**Real admin CRUD** (`/admin/dashboard/cms/cities/`) — mirrors the Feature 11 FAQ pattern exactly: list (stats, Edit/Activate-Deactivate/Delete), separate add/edit form. Deactivating a city removes it from the dropdown without deleting it (useful if a city's listings dry up temporarily); deleting removes the row outright — existing `Property`/`RoommatePosting` rows with that city text are completely unaffected either way, since there's no FK. Every action audit-logged via the existing `log_admin_action()` helper. Added as a new "Cities" card on the CMS Management hub, alongside Content Blocks/Legal Pages/Site Settings/SEO Settings.

## A mistake made and caught during this build

While creating `core/forms.py` for the new `CityForm`, I used the Write tool without first checking whether the file already existed — it did (`ContactForm`/`NewsletterForm`, used by the real Contact page and Home newsletter signup), and my Write silently overwrote it. Caught immediately via `python manage.py check` failing on an import error, recovered the original content from `git show HEAD:core/forms.py`, and re-added `CityForm` alongside the restored originals rather than losing them. Lesson: always Read a file before Write, even when creating what seems like a "new" per-feature form module — check the directory listing result, don't assume based on the file's apparent purpose.

## Files

**Backend**: `core/models.py` (`City`), `core/admin.py`, `core/forms.py` (`CityForm`, alongside the pre-existing `ContactForm`/`NewsletterForm`), `core/migrations/0002_city.py` + `0003_seed_cities.py`; `properties/views.py` (`get_city_options()` replacing `CITY_OPTIONS`), `core/views.py` (updated import/usage); `dashboard/views.py` (`admin_cities`, `admin_city_form`, `admin_city_delete`, `admin_city_toggle`), `dashboard/urls.py`, `dashboard/context_processors.py`.

**Templates**: `dashboard/templates/dashboard/admin_cities.html` (new), `admin_city_form.html` (new), `admin_cms_faqs.html` (+Cities hub card), `_sidebar_admin.html` (active-state update).

**Tests**: `core/tests.py` — `CityOptionsTests` (seed carried forward correctly, `get_city_options()` filters/orders correctly, the search page renders a newly-added city, a property can still be listed in a city outside the curated list) and `AdminCityManagementTests` (add/toggle/delete, access control).

## Verification

- `python manage.py check` — clean.
- `python manage.py test core dashboard properties` — run to confirm no regressions from the `CITY_OPTIONS` → `get_city_options()` swap.
- Manual: Admin → CMS Management → Cities → Add City → new city immediately appears in the Home and Search Results dropdowns with no restart/deploy.
