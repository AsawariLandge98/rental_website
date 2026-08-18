# Feature 12 — Subscription Plans + Razorpay Payments

**Status:** Done and tested (scaffolding — real checkout needs test-mode keys added by the user)
**Maps to:** Workflow doc, Part 12 — Subscriptions

## What this feature does

The last remaining admin stub that couldn't be built from real data alone was Payments/Subscription Plans — unlike every other Feature 06-11 stub, it needed an actual billing decision, which was asked about explicitly (twice — once on the general approach, once on the gateway) rather than assumed, consistent with the Feature 07 verification-gate precedent. Confirmed: **real Razorpay integration, test mode**, and **scaffolding built first with placeholder env var names — real test-mode keys to be added later**, so the build wasn't blocked on an external account signup.

There was already an empty `subscriptions` app registered in `INSTALLED_APPS` but never filled in or mounted — the same shape `cms`/`inquiries`/`visits`/`notifications` were before their respective features. This is its home.

- **New models** (`subscriptions/models.py`): `SubscriptionPlan` (admin-managed catalog — name, price, listing limit, priority flag, features), `Subscription` (one active-or-past record per owner), `Payment` (one row per Razorpay transaction attempt). Seeded with 4 real plans (Free ₹0 / Silver ₹499 / Gold ₹999 / Premium ₹1999) via a data migration — real, usable pricing from day one, not empty tables.
- **Owner Subscription Plan** (`/owner/dashboard/subscription/`) — real plan comparison cards, current subscription status, Razorpay Checkout.js integration.
- **Admin Subscription Plans** (`/admin/dashboard/subscriptions/`) — real CRUD (add/edit/activate/deactivate), same list+form shape as Feature 11's CMS FAQ management.
- **Admin Payments** (`/admin/dashboard/payments/`) — real, read-only transaction ledger: stats, search, status filter, pagination.
- **A real, additive enforcement**: `properties/manage_views.py::start_listing` now checks the owner's plan's `listing_limit` and blocks creating a new draft past it, redirecting to the Subscription page with an honest message. Owners with no subscription default to whichever plan sorts first (the seeded Free plan, limit 3) — looked up from the database, not a hardcoded number, so it stays correct if the Free plan's limit is ever changed by an admin.
- Every admin action on plans logs to the Feature 10 Audit Log via the existing `log_admin_action()` helper.

## The Razorpay flow, and what "scaffolding first" means

Standard Checkout.js flow, which works on localhost with no public URL:
1. Owner clicks Subscribe → server creates a real Razorpay Order + a local `Payment` row (`status=created`).
2. Razorpay's Checkout.js widget opens client-side with that order.
3. On success, Razorpay's JS callback POSTs the payment ID/order ID/signature back to a same-site verification endpoint.
4. Server verifies the HMAC signature (`razorpay.Client.utility.verify_payment_signature`, using the secret key — never exposed client-side), activates a real `Subscription`.

**Right now `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` are blank** (added as empty placeholders to `.env`/`.env.example`, read via `os.environ.get(...)` matching the existing `SECRET_KEY`/DB-credential pattern already in `rental_project/settings.py`). Until real test-mode keys are added, the Subscription page shows an honest "Payments aren't switched on yet" banner and every plan's button reads "Not Available Yet" instead of offering a checkout that would just fail. `create_order` returns a clean `503` with a real error message rather than crashing. **To go live in test mode:** sign up for a free Razorpay account, switch to Test Mode, copy the test Key ID + Key Secret from Settings → API Keys, and add them to `.env`.

## A real security fix made during implementation

The naive version of this flow has a genuine vulnerability: Razorpay's signature only proves *some* order/payment pair is authentic — it does **not** prove it's the order created for *this* local `Payment` row. Without an extra check, a real signature from a cheap plan's checkout could be replayed against a different local `Payment` row pointing at a more expensive plan, activating it without paying the difference. `verify_payment` explicitly checks `razorpay_order_id == payment.razorpay_order_id` **before** even calling Razorpay's signature verification — tested directly (`test_order_id_mismatch_is_rejected_before_touching_razorpay`).

## Deliberate v1 simplifications (flagged, not silently dropped)

- **No webhook endpoint.** Webhooks need a publicly reachable URL (ngrok or similar in local dev) and mainly cover the edge case of the browser closing before the JS success callback fires. The redirect+verify flow above is the complete, correct path for the common case.
- **No refund processing** in the admin Payments page — it's read-only. Real refunds need Razorpay's Refund API and a UI for it; deferred.
- **No auto-recurring billing.** `Subscription.current_period_end` is a real 30-day window from activation, but nothing auto-charges when it lapses — the owner subscribes again manually. A real recurring-billing integration (Razorpay Subscriptions, not one-off Orders) is a bigger, separate piece of work.
- **`Property.listing_plan` (the existing per-listing display badge from Feature 02) is untouched.** The new `Subscription.plan.listing_limit` is a separate, additive enforcement layer, not a replacement — avoids regression risk on already-shipped, tested Feature 02 code.

## How it was tested

**Automated** — 162 tests total across the project (`python manage.py test`), including new `subscriptions/tests.py` (seed data is real, access control, the gateway-not-configured path returns a clean error instead of a 500, order creation with a mocked Razorpay client creates a real `Payment`, the order-ID-mismatch security check, invalid-signature handling, a fully mocked valid payment activates a real `Subscription`, and a repeated verify call is idempotent — no double-`Subscription` bug), plus new tests in `dashboard/tests.py` (admin Subscription Plans CRUD + audit logging, admin Payments access/stats/filtering) and `properties/tests.py` (the listing-limit actually blocks a 4th listing, both GET and POST). No real network calls to Razorpay are made in tests — the client is mocked throughout.

**Manual** — ran the dev server, drove it with Playwright: confirmed the owner Subscription page shows all 4 real seeded plans with the honest "not configured" state; found and fixed one real content bug this way — the Gold and Premium plan cards showed "Priority placement" twice (once auto-rendered from the `priority_listing` flag, once duplicated in the seeded `features` text) — fixed the seed migration and reapplied it. Exercised the full admin plan create → deactivate flow and confirmed both actions landed in the Audit Log. Set up a disposable test owner at exactly the Free plan's 3-listing cap and confirmed `/properties/manage/new/` really redirects to the Subscription page with the limit message instead of creating a 4th draft — then deleted the disposable account.

### Try it yourself

As `owner@example.com` / `StrongPass123`: Subscription Plan in the sidebar. As `admin@example.com` / `AdminPass123` (Super Admin): Subscription Plans and Payments in the sidebar. Real checkout won't work until Razorpay test-mode keys are added to `.env` — see above.

## Files touched

`subscriptions/models.py`, `forms.py`, `views.py`, `urls.py`, `admin.py`, `tests.py` (new/filled in), `subscriptions/migrations/0001_initial.py` + `0002_seed_plans.py` (new). `rental_project/urls.py` (mounted `subscriptions.urls`), `rental_project/settings.py` (+`RAZORPAY_KEY_ID`/`SECRET`), `.env`/`.env.example` (+ placeholders), `requirements.txt` (+`razorpay` and its transitive deps). `properties/manage_views.py` (`_owner_listing_limit` helper + `start_listing` enforcement), `properties/tests.py` (new test). `dashboard/views.py` (removed `payments`/`subscriptions`/`subscription` stub entries; added `admin_subscriptions`, `admin_subscription_plan_form`, `admin_subscription_plan_toggle`, `admin_payments`), `dashboard/urls.py`, `dashboard/tests.py` (`AdminSubscriptionsTests`, `AdminPaymentsTests`), `dashboard/templates/dashboard/owner_subscription.html`, `admin_subscriptions.html`, `admin_subscription_plan_form.html`, `admin_payments.html` (new), `_sidebar_owner.html`/`owner_home.html` (point to the real `subscriptions:plan_list` URL instead of the old stub). `static/css/dashboard.css` (`.plan-grid`/`.plan-card*` components).

## What's next

**Admin Roles & Permissions (granular RBAC)** is the one remaining piece of the original Super Admin panel batch — every other stub is now either built or intentionally deferred with a stated reason. It would touch every existing `admin_required`-gated view built across Features 06-12.
