# Feature 13 — Admin RBAC (Admin vs Super Admin)

**Status:** Done and tested
**Maps to:** Workflow doc, Part 17 — System Settings & Security (partial)

## What this feature does

The last remaining piece flagged across Features 06-12 was granular Admin RBAC — the original screenshots described several named admin roles (Property Manager, Finance Admin, Verification Manager, etc.) each with a module-level permission matrix, which would mean new Role/Permission models and retrofitting real permission checks onto every one of the ~25 admin views built so far. Before touching anything, this was asked about explicitly, since it's the most invasive remaining piece and the screenshots themselves disagreed on what the roles should even be (a mockup-inconsistency pattern already seen a few times this build). Confirmed: **keep it simple — Admin vs Super Admin only**, with one real, meaningful difference: **only Super Admin can manage other admin accounts and touch platform-wide Settings.**

- **New `super_admin_required` decorator** (`dashboard/decorators.py`) — stricter than the existing `admin_required`, checks `role == SUPER_ADMIN` specifically.
- **Admin Users** (`/admin/dashboard/admin-users/`, Super-Admin-only) — real management of who has Admin/Super Admin access: a list (separate from Feature 06's public-facing User Management, which explicitly excludes internal roles), **Add New Admin** (a real, immediately-usable account — full name, email, mobile, role, password, created directly, no invite-email flow), **promote/demote** between Admin and Super Admin, **activate/deactivate**.
- **Settings** — the one remaining stub — is now gated `super_admin_required` instead of `admin_required`. Its sidebar link (along with the new Admin Users link) is hidden entirely from regular Admins, not just blocked after clicking.
- Every action (create, role change, activate/deactivate) logs to the Feature 10 Audit Log.

## Safety guards, and a real thing I learned about them while testing

Two guards protect against locking everyone out of admin management: you can't act on your own account (must ask another Super Admin), and you can't demote/deactivate the last active Super Admin.

Writing the test for the second guard surfaced something worth recording: **it can never actually trigger through this app's own web UI** in the current single-actor-per-request model. To reach the `@super_admin_required` decorator at all, the acting user must themselves be an authenticated, active Super Admin — which means at the moment they act on a *different* Super Admin, that target is never really "the last one," because the actor is still there. The guard only matters as **defense-in-depth against other pathways** — most concretely, Django's own `/admin/` site, which already lets a superuser edit any `User.is_active` field directly and isn't restricted by this app's checks at all. The test reflects this honestly: it calls the `_is_last_active_super_admin()` helper directly rather than pretending a request-cycle scenario is reachable when it provably isn't.

(A first attempt at testing this the "obvious" way — deactivate the account, then `force_login()` as it anyway to isolate the guard — didn't work and is worth remembering: Django's session auth backend re-validates `is_active` on **every** request via `ModelBackend.get_user()`, not just at login time, so `force_login()` on an inactive user gets silently treated as anonymous on the very next request. There's no way to fake "authenticated but inactive" through the normal request cycle.)

## Deliberate scope

No new Role/Permission models, no per-module permission matrix, no admin sub-roles (Property Manager, Finance Admin, etc.) — that's the invasive version explicitly declined. Admin and Super Admin remain the only two internal roles, already defined since Feature 01; this feature only adds one real behavioral difference between them plus the tooling to manage who holds which.

## How it was tested

**Automated** — 173 tests total across the project (`python manage.py test`), including new `AdminInternalUsersTests` in `dashboard/tests.py`: access is Super-Admin-only (both for the page and, separately, for Settings), stats are correct, a created admin account is real and immediately usable for login, mismatched passwords are rejected, promote/demote round-trips correctly, self-action is blocked (role and deactivate both), deactivating actually prevents login, and every action lands in the Audit Log. The `_is_last_active_super_admin()` helper is tested directly, for the reason above.

**Manual** — ran the dev server, drove it with Playwright as `admin@example.com` (Super Admin): confirmed the Admin Users list shows only the real seeded account, walked through the full create → promote → demote → deactivate round-trip on a disposable test account, and confirmed all four actions appeared correctly in the Audit Log in order. Then created a genuine Admin-role (not Super Admin) test account and confirmed, logged in as it: the Admin Users and Settings sidebar links are **not rendered at all**, and direct navigation to either URL returns a real `403`. All disposable test accounts and their audit log entries were deleted afterward — unlike Features 07/09 (where test actions touched real, persistent, meaningful entities worth keeping a record of), this account existed purely for this test, so removing its trail too keeps the audit log meaningful rather than cluttered with fake identities.

### Try it yourself

Log in as `admin@example.com` / `AdminPass123` (Super Admin) — Admin Users and Settings appear in the sidebar. Any other role, or a regular Admin account, won't see either link and gets a real 403 on direct navigation.

## Files touched

`dashboard/decorators.py` (+`super_admin_required`), `dashboard/forms.py` (+`AdminCreateForm`), `dashboard/views.py` (removed the now-empty `ADMIN_COMING_SOON_SECTIONS`/`admin_coming_soon`, replaced with a dedicated `admin_settings_stub`; added `admin_internal_users`, `admin_user_create`, `admin_user_set_role`, `admin_user_set_active_internal`, `_is_last_active_super_admin`), `dashboard/urls.py` (new routes, `admin_settings` repointed), `dashboard/tests.py` (`AdminInternalUsersTests`; also cleaned up a stale test that had drifted out of sync with reality across Features 07-12 — it was still named "coming soon sections" but 8 of its 9 checked routes were real pages by now), `dashboard/templates/dashboard/admin_internal_users.html`, `admin_user_create.html` (new), `_sidebar_admin.html` (Admin Users + Settings now conditionally rendered, Super-Admin-only).

## What's next

Every module from the original Super Admin screenshot batch is now either built for real or intentionally, explicitly deferred with a stated reason (no webhooks/refunds/auto-billing in Payments; no granular per-module RBAC here). Remaining gaps across the whole project: Roommate/Hotel detail pages, decorative search filter checkboxes, and Reviews — none of which came from the admin panel batch.
