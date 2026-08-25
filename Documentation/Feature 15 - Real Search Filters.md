# Feature 15 — Real Property Search Filters

**Status:** Done and tested
**Maps to:** Part 5 (Property Search) — the sidebar "Filters" panel on `/properties/`, which existed visually since Feature 04 but never affected results

## What this feature does

The Search Results sidebar (Budget Range slider, Property Type / Bedrooms / Furnishing checkboxes) was pure decoration — none of the checkboxes had a `name` attribute, the range slider inputs weren't submitted at all, and several checkboxes were hardcoded `checked` for visual demo purposes only (an "All Types" box, a "2 BHK" box) with no relationship to what was actually shown. Only the top toolbar (City/Area/Property Type dropdown/Budget bucket) and sort/pagination were real, going back to Feature 04.

This wires the whole filters panel to the real `Property` model fields — no new UI, no new model, just making already-shown controls actually filter:

- **Property Type checkboxes** — now render the real `Property.PropertyType.choices` (8 real types) instead of a hardcoded 5-item list that included "PG / Hostel," which isn't a real type on this model. Multi-select, OR'd together.
- **Bedrooms checkboxes** — real `bedrooms` field: Studio (`property_type=studio` or `bedrooms=0`), 1/2/3 BHK exact match, 4+ BHK (`bedrooms__gte=4`).
- **Furnishing checkboxes** — real `Property.FurnishingStatus.choices` (Fully/Semi/Unfurnished), a 1:1 match with what was already there.
- **Budget Range slider** — the dual-handle drag JS was already fully real (`initBudgetRangeSlider` in `main.js`); it just had no `name` attribute so its values were silently discarded on submit. Now submits `price_min`/`price_max`.

**How two separate `<form>`s share one submission:** the top toolbar and the sidebar panel are visually and structurally distinct (the sidebar is a CSS grid sibling of the results column, and on mobile becomes a fixed-position drawer), so merging them into one nested DOM tree wasn't practical. Instead the toolbar `<form id="searchForm">` stays the only `<form>` element, and every sidebar checkbox/slider input uses the HTML5 `form="searchForm"` attribute to submit with it regardless of DOM position — one real GET request, no hidden-input duplication, no param collisions between the toolbar's single-value Property Type dropdown and the sidebar's multi-value checkboxes (both use `getlist('property_type')` server-side, so either or both can contribute values in one submission).

**A default-value trap, avoided deliberately:** because the slider's range inputs always have *some* value (unlike checkboxes, which contribute nothing unless checked), giving them non-zero example defaults (the original mockup showed handles at ₹10,000–₹30,000) would have silently applied that as a real filter on every plain toolbar search, even one that never touched the slider. Fixed by defaulting the handles to the full 0–100,000 range and treating both extremes as "no filter" server-side — only a value the user actually dragged in from an edge does anything.

## Deliberate scope

**Roommates and Hotels were explicitly left out of this feature**, despite being named alongside Search in the standing backlog item. Investigating both before starting revealed they have **no real backing model at all** — `roommates/views.py` and `hotels/views.py` are still 100% hardcoded Python list literals (fake names, `pravatar.cc` avatar URLs, fake locations) from before this rebuild started, and their own filter dropdowns (City, Area, Budget, Room Type, Gender) are hardcoded to a single fake `<option>` each — not just the checkboxes, the entire page. Wiring their filters for real would mean building a real `RoommateProfile`/hotel-equivalent model and a real listing-creation flow first — a new feature on the scale of Properties (Feature 02), not a filter-wiring task. Flagging this rather than either silently expanding scope into a multi-hour build or silently faking a smaller version of it.

## How it was tested

**Automated** — new `SearchAdvancedFiltersTests` in `properties/tests.py` (5 tests): multi-select Property Type checkboxes OR correctly, Bedrooms handles both the `studio` and `4plus` special cases, Furnishing filters on the real enum values, and the price slider both filters correctly at a real range and is confirmed to be a no-op at its full-range defaults (so a plain search never gets a hidden, unintended price cap). Full suite: 184 tests passing.

**Manual** — no browser automation tool was available this session, so verification was done via Django's test client against rendered HTML: submitted a combined filter set (`property_type=villa&property_type=room&bedrooms=2&furnishing=fully_furnished&price_min=20000&price_max=60000`) and confirmed the response both filtered correctly and re-rendered the exact right checkboxes as `checked` on reload — round-trip state, not just one-way filtering.

## Files touched

`properties/views.py` (`search_results` — real multi-value filtering for property type/bedrooms/furnishing/price range, `BEDROOM_OPTIONS`/`PRICE_SLIDER_MIN`/`PRICE_SLIDER_MAX` constants), `properties/templates/properties/search_results.html` (checkboxes and range inputs now carry real `name`/`value`/`checked` state and a `form="searchForm"` attribute; the per-page mini-form's hidden-input carry-forward switched from `request.GET.items` to `request.GET.lists` — the former silently drops all but the last value of a multi-valued param, which would have quietly broken "change results-per-page" whenever more than one checkbox was active), `properties/tests.py` (+`SearchAdvancedFiltersTests`).

## What's next

Roommate/Hotel detail pages, Roommate/Hotel real filtering (blocked on real models existing first, per above), and Reviews remain — none have a prior screenshot on file in this conversation to build the UI against.
