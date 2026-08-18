# Feature 11 — CMS Management (FAQs)

**Status:** Done and tested
**Maps to:** Workflow doc, Part 16 — CMS

## What this feature does

Continuing the "make next" build-out, this closes out **CMS Management** — picked over the other two remaining candidates (Payments/Subscriptions still needs a real payment-gateway decision that shouldn't be assumed; Admin Roles & Permissions would touch every existing admin view built across Features 06-10) because it's buildable safely and additively.

There's already an empty `cms` app registered in `INSTALLED_APPS` — a stub in exactly the same shape `inquiries`/`visits`/`notifications` were before Feature 03 filled them in. And the site already had two **hardcoded** FAQ lists doing real work: `CONTACT_FAQS` in `core/views.py` (5 items, public Contact page) and `FAQS` in `dashboard/views.py` (8 items, Tenant Help & Support page). Rather than invent generic "content blocks," this feature makes exactly that already-real content admin-editable — a clean, contained first CMS slice.

- **New `cms.FAQ` model** — question, answer, `placement` (Contact Page / Tenant Help & Support), display order, published flag. A data migration (`cms/migrations/0002_seed_faqs.py`) copies the **exact existing 13 FAQ entries** verbatim into real rows — nothing was reset to empty or replaced with placeholder text.
- **Admin CMS Management** (`/admin/dashboard/cms/`) — real list (stats, search, placement filter, pagination), Add/Edit form, Publish/Unpublish toggle, Delete (with confirmation). Every action is logged to the Feature 10 Audit Log.
- **Both public-facing pages now read from the database** instead of a hardcoded Python list — `core/views.py::contact` and `dashboard/views.py::help_support` both query `FAQ.objects.filter(placement=..., is_published=True)`.

## Deliberate scope

- **FAQs only, not a generic CMS.** The screenshots implied a broader CMS (homepage content, policies, announcements) — building a generic rich-content system now would mean either a vague catch-all "Page" model with no real structure, or restructuring already-polished, carefully-designed templates (About/Contact/Home got a full UI/UX pass in Feature 04) into many small editable fields, both bigger and riskier than the value justifies right now. FAQs were the one piece of content that was *already* a clean, structured list with an obvious real editing need.
- **Delete is allowed here, unlike Properties (Feature 07).** FAQ content isn't user data, isn't financial, and is trivial to recreate — none of the reasons Property/User deletion was deliberately left out apply here.

## How it was tested

**Automated** — 143 tests total across the project (`python manage.py test`), including new `FAQPublicRenderingTests` in `cms/tests.py` (contact page shows only published Contact-placement FAQs; the seed migration actually populated real content, not an empty table) and `AdminCmsFaqTests` in `dashboard/tests.py` (access control, create/edit/toggle/delete, search + placement filtering, and that every action lands in the Feature 10 audit log).

**Manual** — ran the dev server, drove it with Playwright: confirmed the public Contact page and the Tenant Help & Support page both render all their real, migrated FAQ content (the Contact page's FAQ section briefly showed empty in a naive full-page screenshot — this is the known `data-reveal` scroll-animation behavior documented from Feature 04's QA notes, not a bug; scrolling to it and re-checking confirmed all 5 items render correctly). Walked through the full CRUD round-trip in the admin panel (create → unpublish → edit → delete) and confirmed each step both took effect on the list page and produced a real Audit Log entry.

### Try it yourself

Log in as `admin@example.com` / `AdminPass123` (Super Admin), then CMS Management in the sidebar. Public-facing: `/contact/` and (as a tenant) `/tenant/dashboard/help/`.

## Files touched

`cms/models.py` (+`FAQ`), `cms/forms.py` (new, `FAQForm`), `cms/admin.py` (+`FAQAdmin`), `cms/migrations/0001_initial.py` + `0002_seed_faqs.py` (new, data migration preserves the real existing content), `cms/tests.py` (new). `core/views.py` (`contact` view queries `FAQ` instead of a hardcoded list), `core/templates/core/contact.html` (`faq.q`/`faq.a` → `faq.question`/`faq.answer`). `dashboard/views.py` (`help_support` queries `FAQ`; added `admin_cms_faqs`, `admin_cms_faq_form`, `admin_cms_faq_delete`, `admin_cms_faq_toggle`; removed the `cms` stub section), `dashboard/templates/dashboard/help_support.html` (loop over model instances instead of tuples), `dashboard/urls.py` (real CMS routes), `dashboard/tests.py` (`AdminCmsFaqTests`), `dashboard/templates/dashboard/admin_cms_faqs.html`, `admin_cms_faq_form.html` (new).

## What's next

Payments/Subscription Plans (needs a real payment-gateway decision) and Admin Roles & Permissions (granular RBAC, the last big deferred structural piece — would touch every admin view built so far) are the two remaining unbuilt pieces of the Super Admin panel.
