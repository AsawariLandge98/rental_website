# Feature 10 — Admin Audit Logs

**Status:** Done and tested
**Maps to:** Workflow doc, Part 9 — Admin Dashboard (partial) / Part 17 — System Settings & Security (partial)

## What this feature does

Continuing the "make next... real data" build-out from Feature 09, this closes out **Audit Logs** — one of the two biggest structural pieces flagged as deferred across Features 06-09. Picked over the two other remaining candidates (Payments/Subscriptions, which need a real billing/gateway decision first, and CMS Management, which needs deciding what counts as "content") because an audit log is inherently, unavoidably real data: every entry is just a record of an admin action that already happened. There's no way to fake one without it being pointless.

- **New `AuditLog` model** (`dashboard/models.py`) — append-only by design. `target_repr`/`target_id`/`target_type` are plain values, not a foreign key, so a log entry survives the target row being changed or deleted later (the whole point of an audit trail is that it doesn't get quietly erased along with what it's describing). Registered in Django admin as **read-only** — `has_add_permission`/`has_change_permission`/`has_delete_permission` all return `False`, so even a superuser can't edit or delete entries through Django's own admin site, only through the app's normal database access.
- **Admin Audit Logs** (`/admin/dashboard/audit-logs/`) — real-time list of every logged action, stats (Total/Today/This Week), search (action text/admin name) + target-type filter, pagination. Property-targeted entries link through to that property's admin detail page (Feature 07).
- **Every existing admin moderation action now logs a real entry**: Block/Unblock user (Feature 06), Approve/Reject/Pause/Resume/Archive property (Feature 07), Close/Reopen inquiry, Cancel visit (Feature 08), Resolve/Reopen support ticket (Feature 09) — 7 call sites total, each a one-call addition (`log_admin_action(...)`, mirroring the existing `notifications.notify()` helper pattern) with no change to the action's existing behavior.

## How it was tested

**Automated** — new `AdminAuditLogTests` class in `dashboard/tests.py`: access control, one test per logged action type confirming the log entry's admin/message/target content is correct (including that a rejection reason actually appears in the log message), stats and search/filter correctness on the list view, and a direct test that `AuditLogAdmin`'s three permission methods all return `False` (so the append-only guarantee itself has coverage, not just the logging behavior).

**Manual** — ran the dev server, drove it with Playwright as `admin@example.com`: confirmed the empty state first (honestly zero entries, since no admin actions had happened since this feature's migration), then performed a real Block → Unblock round-trip against the documented `tenant@example.com` seed account (safe and reversible — the exact account/flow already covered by Feature 06's automated tests) and confirmed both actions appeared as real, correctly-ordered, correctly-timestamped log entries. Verified the account was left active afterward. No console errors at 1440px or 390px widths.

### Try it yourself

Log in as `admin@example.com` / `AdminPass123` (Super Admin), then Audit Logs in the sidebar. Perform any moderation action elsewhere in the admin panel (block a user, approve a property, resolve a ticket) and it'll appear here immediately.

## Files touched

`dashboard/models.py` (+`AuditLog`, `log_admin_action` helper), `dashboard/migrations/0002_auditlog.py` (new), `dashboard/admin.py` (`AuditLogAdmin`, read-only), `dashboard/views.py` (`admin_audit_logs` view; `log_admin_action(...)` call added to all 7 existing admin moderation views), `dashboard/urls.py` (new route), `dashboard/tests.py` (`AdminAuditLogTests`), `dashboard/templates/dashboard/admin_audit_logs.html` (new), `_sidebar_admin.html` (new "Audit Logs" nav item, positioned after CMS Management).

## What's next

Payments/Subscription Plans (needs a real payment-gateway decision) and CMS Management (needs deciding what static content becomes admin-editable) are the two remaining "Coming Soon" stubs. Admin Roles & Permissions (granular RBAC — different admins with different capabilities) is the last big deferred structural piece; interestingly, Audit Logs would pair naturally with it once built (logging *which* admin role performed an action becomes more meaningful once roles actually differ).
