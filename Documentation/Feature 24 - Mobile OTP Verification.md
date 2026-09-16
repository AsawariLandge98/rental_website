# Feature 24 — Mobile OTP Verification

## Context

Next item off the "important, not yet built" list. `User.mobile_number` and `User.is_mobile_verified` have existed since early on, and `is_mobile_verified` was already displayed in two places (the `profile.html` verify-pill, the listing-wizard sidebar checklist) — but nothing ever set it to `True`. It was pure decoration.

Scoping question asked before building: which SMS gateway to integrate against. User's answer: **"Abhi decide nahi, scaffolding hi bana do"** — don't decide the provider yet, just build the scaffolding. Same "scaffolding first, keys later" pattern as Razorpay/Google OAuth/S3/Email, with one difference worth calling out: unlike SMTP (one standard protocol every email provider speaks), SMS gateways each have their own REST API shape. Rather than guess a specific provider's exact request format, `core/sms.py::send_sms()` is a small, deliberately generic wrapper — the OTP model, rate-limiting and verification logic are all fully real and provider-independent; only `send_sms()`'s internals need adjusting once a real gateway is chosen.

Built as **self-service and optional** — not a registration gate — consistent with how `is_email_verified` already works and with the site's low-friction-by-default convention. Any logged-in user (tenant/owner/hotel/admin) can verify their own number from Settings or Profile whenever they choose.

## What was built

**`accounts.MobileOTP`** — one row per send attempt: `user` FK, `mobile_number`, 6-digit `code`, `attempts`, `is_used`, `created_at`, `expires_at`. `OTP_VALID_MINUTES = 10`, `MAX_ATTEMPTS = 5`. Resending invalidates any still-unused prior code for that user, so "latest unused, unexpired, under-attempt-limit code" is always the one row that can pass verification.

**`core/sms.py`** — `send_sms(mobile_number, message)`, generic REST POST (`api_key`/`sender_id`/`mobile`/`message`) to a configurable `SMS_API_URL`. Raises `SMSSendError` on failure; never called at all unless `settings.SMS_CONFIGURED` is true.

**`settings.py` scaffolding** (mirrors `EMAIL_CONFIGURED`/`GOOGLE_OAUTH_CONFIGURED` exactly): `SMS_API_URL`/`SMS_API_KEY`/`SMS_SENDER_ID` from env (blank by default), `SMS_CONFIGURED = bool(SMS_API_URL and SMS_API_KEY)`.

**Dev-safe fallback** — with no gateway configured (the current, real state), `mobile_verify_send` doesn't call `send_sms()` at all: it generates and stores a real OTP row, then surfaces the code directly via a Django message ("SMS gateway not configured yet — your code is 123456 (dev mode)"). Same role console `EMAIL_BACKEND` played for password reset before real SMTP existed — the whole verify flow is testable locally today, with zero external account. Once real credentials exist, this branch is skipped entirely and the code is never shown in the response (verified by test).

**Real rate limiting** — a resend cooldown (60s) and a per-user hourly cap (5 sends/hour), both via Django's cache framework, same mechanism as the Feature 19 login lockout. A wrong-code counter on the OTP row itself invalidates the code after 5 failed attempts.

**Entry points**:
- `profile.html` — the existing "Mobile Not Verified" pill is now a real link to the verify flow when unverified (plain "Mobile Verified" pill, unchanged, once it's true).
- `settings.html` / `owner_settings.html` — the Mobile Number row gets a real "Verify" link (unverified) or a "Verified" status pill, covering tenant, owner and hotel accounts (both templates share the same markup).

**The verify page** (`accounts/templates/accounts/mobile_verify.html`) — a real two-step flow inside the dashboard shell: "Send Verification Code" button, then a 6-box OTP entry (auto-advance/backspace/paste handling, vanilla JS) with a resend link. Reuses the `.otp-row`/`.otp-box`/`.fp-hero`/`.fp-resend` CSS that had sat fully styled but completely unused in `auth.css` since earlier work — the first template to actually consume it. A small `.btn-link` class was added for the resend button (didn't exist before).

**Safe redirect** — reuses the existing `_safe_next_url()` helper from login/registration; every entry point passes `?next=<current page>` so verifying returns the user exactly where they started, with a role-aware settings-page fallback (`SETTINGS_URL_NAME_BY_ROLE`) if `next` is absent.

## Deliberately scoped out this pass

- No SMS gateway is actually wired up — `SMS_CONFIGURED` is false until the user adds real `SMS_API_URL`/`SMS_API_KEY` to `.env`.
- Not a registration gate, no "verify before you can list/inquire" enforcement anywhere — purely a self-service trust signal, matching `is_email_verified`'s existing scope.
- `core/sms.py`'s payload shape is a reasonable generic default, not verified against any specific provider's real docs (none chosen yet) — flagged in-code as the one function to adjust once a gateway is picked.

## Files

**Backend**: `accounts/models.py` (`MobileOTP`), `migrations/0006_mobileotp.py`, `accounts/admin.py` (`MobileOTPAdmin`, read-only-in-spirit), `accounts/views.py` (`mobile_verify_send`, `mobile_verify_confirm`, `SETTINGS_URL_NAME_BY_ROLE`), `accounts/urls.py`, `core/sms.py` (new), `rental_project/settings.py` (`SMS_*` block), `.env` / `.env.example`.

**Templates**: `accounts/templates/accounts/mobile_verify.html` (new), `dashboard/templates/dashboard/profile.html`, `settings.html`, `owner_settings.html`.

**CSS**: `static/css/auth.css` (`.btn-link`, new), `static/css/dashboard.css` (`a.verify-pill` link styling).

**Tests**: `accounts/tests.py` — `MobileVerificationTests` (login required, missing-mobile-number rejected, already-verified short-circuits, dev-mode code shown in message, resend cooldown blocks immediate resend and preserves the original code, resend after cooldown invalidates the old code, correct code verifies, incorrect code doesn't, too-many-attempts invalidates the code, and — via `@override_settings(SMS_CONFIGURED=True)` + mocked `send_sms` — the configured path calls the gateway and never leaks the code into the response, and a gateway failure is handled gracefully instead of crashing).

## Verification

- `python manage.py test accounts` — 34 tests pass.
- `python manage.py test` (full suite) — run in background; see session notes for the final count.
- Manual: with `.env` SMS vars blank, Settings → Verify → code appears on-screen (dev mode), entering it flips the pill to Verified immediately; resending within 60s is blocked; 5 wrong attempts locks the code and a fresh one is required.
