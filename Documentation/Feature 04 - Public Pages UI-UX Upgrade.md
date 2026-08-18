# Feature 04 — Public Pages UI/UX Upgrade

**Status:** Done and tested
**Scope:** Site-wide craft/polish pass, Phase 1 (public pages) — Home, About, Contact, Roommate Finder, Hotels & Homestays, Search Results, Property Detail

## Why this happened

After Feature 03 (Tenant Dashboard), the user asked for a top-tier (Google/Apple/Amazon-caliber) UI/UX pass across the whole site, with explicit permission to touch backend too so nothing is just "for show." Two things were confirmed up front: keep the existing navy-blue "trust" palette and Poppins/Inter type system (craft upgrade, not a rebrand), and do public pages first before Auth, the Listing Wizard, and further Tenant Dashboard polish.

Investigating the public pages before touching anything turned up more than cosmetic gaps — several pages had dead, decorative-only UI that looked functional but wasn't, and some content made claims that aren't true. Both are addressed here, not just visual polish.

## Real bugs fixed (not just polish)

- **Home's Quick Search form did nothing** (`action="#"`) — now submits to the real `/properties/` search with matching field values (city/property type/budget options are now pulled from the same source as the real Search page, instead of a hand-typed list that didn't match the real filter values — e.g. the old Property Type options like `"flat"`/`"pg"` didn't match any real `Property.property_type` choice, so the form would have silently returned zero results even if wired up naively).
- **Home's Featured Properties was 4 hardcoded fake listings**, completely disconnected from the real `Property` model. Now queries real published listings (newest first), with a proper empty state for a fresh database instead of an empty grid.
- **Newsletter forms did nothing** (Home, About, Hotels sidebar) — new `core.NewsletterSubscriber` model + a real subscribe endpoint, with success/duplicate/invalid-email feedback.
- **Contact form had no `name` attributes and no submit handling** — new `core.ContactMessage` model + real validation and submission (visible/actionable in Django admin, same "no live support agent, but genuinely saved and real" pattern as the Tenant Dashboard's `SupportTicket`).
- **Fake result counts and fake pagination.** Roommates claimed "342 Roommates Found" with a 18-page paginator while showing 8 real hardcoded entries; Hotels claimed "128 Stays Found" with an 11-page paginator showing 4. Both now show the real count with pagination removed (there's nothing to paginate with 4–8 items). The real Search Results page had the same problem — it always showed "1 2 3 … 25" regardless of actual results. That one got **real pagination** instead (Django `Paginator`, `page`/`per_page` params, a real Sort-by dropdown wired to `sort=newest|price_asc|price_desc`), since it's the core functional page and the dataset will actually grow.
- **The entire Roommates page sidebar ("Why Choose Rentora?", "Create Your Profile", "Safety Tips") was rendering with zero CSS** — `.sidebar-card`/`.listing-sidebar` and friends only existed in `hotels.css`, which the Roommates page never loads. Moved that shared block into `properties.css` (which both pages already load) so it actually renders. Fixing this revealed a second bug once the sidebar had its real 300px width back: the roommate card grid (`repeat(4, 1fr)` on wide screens) was squeezed into ~130px-wide cards with genuinely clipped text ("Profile Coming Soon" rendering as "rofile Coming Soo"). The responsive breakpoints were backwards — more columns on *wider* screens even though the container is capped and the grid never actually gets more room past 1200px. Fixed to 2-up by default, 3-up only once the layout stacks to full width below 1023px.
- **Roommates/Hotels "View Details" went to `href="#"`** — there's no detail page (building one needs new models on the scale of Feature 02, already the next roadmap candidate). Rather than a live-looking dead link, these are now disabled-styled "Profile/Details Coming Soon" affordances that don't pretend to work.
- Several other dangling `href="#"` links removed (Roommates "Know More", Hotels "Learn More" safety-tips links, Testimonials "View All Reviews" — none had anywhere real to go).
- **Price formatting bug** (pre-existing, not introduced this pass, but touched again here): `₹18,000.00` instead of `₹18,000` on every property card and detail page — `DecimalField` values keep their stored decimal places through `|intcomma`. Fixed with `|floatformat:"0"` first, site-wide.

## Honesty fixes (matching the precedent already set in Feature 02)

Feature 02 explicitly removed "Verified Property" claims from Search/Property Detail once it was clear no verification system exists. That correction hadn't been applied to Home, About, Roommates, or Hotels — all four had "100% Verified" language, verified-shield icons next to names, or (on About) an entire 5-step "Our Verification Process" section describing mobile/ID/property verification that isn't built. All of it is reworded around what's actually true: zero brokerage, direct owner contact, real owner-posted listings, instant visit scheduling. About's verification section is now "How Rentora Works" — 5 honest steps (Create Account → Real Listings → Direct Contact → Instant Visits → Move In).

## New models

- `core.NewsletterSubscriber` — email (unique), created_at.
- `core.ContactMessage` — name, email, phone, subject, message, created_at.

## Design-system additions (`static/css/base.css`, `static/js/main.js`)

Added once, used everywhere, so the pass reads as one consistent product:
- Motion tokens (`--ease`, `--transition-fast`, `--transition-base`) and a `prefers-reduced-motion` kill-switch.
- `:focus-visible` rings sitewide (previously only form fields had any focus style).
- A consistent card hover-lift (shadow + translateY + subtle image zoom) applied to property/roommate/stay/testimonial cards and every round icon tile across Home/About/Contact.
- An animated accordion (`max-height`/`opacity` transition on `.filter-group__body`) — benefits Search filters, the Tenant Dashboard FAQ, and the new Contact FAQ all from one shared rule.
- `initScrollReveal()` — sections fade/rise into view on first scroll (Home, About, Contact FAQ), via `IntersectionObserver` with a 4-second forced-visible safety timeout so content can never get stuck invisible if something goes wrong, and a `prefers-reduced-motion` no-op.
- `.empty-state` — shared "nothing here yet" component, now used by Home (no listings) and Search Results (no matches), replacing blank grids.
- `.btn.is-disabled` — a button-shaped affordance for a feature that's honestly not built yet, used by the Roommates/Hotels "Coming Soon" cards.

## What's still out of scope (unchanged from before this pass)

Roommate/Hotel detail pages and real backing models — still the next roadmap candidate, not attempted here since it's Feature-02-sized work, not a polish pass. Sidebar filter checkboxes on Search/Roommates/Hotels (Bedrooms, Furnishing, Amenities, etc.) are still decorative — only the top search bar and the now-real sort/pagination affect actual results.

## How it was tested

**Automated** — 74 tests total (`python manage.py test`), 13 new: newsletter signup + duplicate/invalid handling, contact form submission + validation, Home's real-data and empty-state rendering, and 5 new pagination/sort tests on Search Results (default page size, second page, `per_page` override, price-ascending sort, empty-state on zero matches).

**Manual** — ran the dev server and drove it with a headless-browser (Playwright) script across all 7 pages at 1440px and 390px widths, plus a real-scroll simulation (not just a snapshot) to correctly verify the new scroll-reveal and accordion behavior, since a plain full-page screenshot doesn't trigger real scroll/IntersectionObserver events. This caught two real, now-fixed issues: the missing Roommates sidebar CSS, and the roommate-card text clipping described above. (Also worth noting for future visual QA: `position:fixed`/`sticky` elements — the mobile tab bar, the header, bottom sheets — can appear in the wrong place in a Playwright full-page screenshot even when they render correctly for a real scrolling user; confirmed this repeatedly by cross-checking against real-scroll captures and viewport-clipped screenshots before concluding something was a tooling artifact rather than a real bug.)

### Try it yourself

Every page discussed here is public — no login needed. `/`, `/about/`, `/contact/`, `/roommates/`, `/hotels/`, `/properties/`, and any property detail page.

## Files touched

`core/models.py` (new), `core/forms.py` (new), `core/admin.py` (new), `core/views.py` (rewritten), `core/urls.py`, `core/tests.py` (new), `core/migrations/0001_initial.py` (new), `core/templates/core/{home,about,contact}.html`. `properties/views.py` (pagination/sort, `CITY_OPTIONS`/`BUDGET_OPTIONS` reused by Home), `properties/templates/properties/search_results.html`, `properties/tests.py`. `roommates/views.py`, `roommates/templates/roommates/list.html`. `hotels/views.py`, `hotels/templates/hotels/list.html`. `static/css/base.css` (design-system additions), `static/css/pages.css`, `static/css/home.css`, `static/css/properties.css` (accordion animation, pagination styling, shared sidebar block moved in), `static/css/roommates.css` (grid breakpoint fix), `static/css/hotels.css` (shared sidebar block moved out). `static/js/main.js` (`initScrollReveal`, `initSortSelect`).

## What's next

Per the confirmed priority order: Auth pages (Login/Register/Forgot Password), the Property Listing Wizard, and a fresh craft pass on the Tenant Dashboard built in Feature 03 — same "keep the palette, fix anything that's actually broken along the way" approach.
