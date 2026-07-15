# Session Log — ai-stock-alert

Entries are newest-first. Each entry documents one Claude Code working session.

---

<!-- New entries go above this line -->

## Session: 2026-07-15

### Accomplished

- Found and fixed a ~13h production outage: PR #18's merge resolution had shipped the old Twilio `send_whatsapp.py` back to prod (import crash, HTTP 500 on every request). Restored the Meta implementation + kept `KV_REST_API_*` env naming (PR #19); verified live.
- Rotated the Meta System User token after transcript exposure: revoke-all → fresh never-expiry token → Vercel prod env → redeploy → verified end-to-end (Meta's "Revoke tokens" is all-or-nothing per System User; revoke FIRST, then generate).
- Security sweep: git history clean (no secrets ever committed); confirmed the three externally-rolled tokens are all Cloudflare — zero impact on this repo's stack.
- Display name "CushLabs" APPROVED (`name_status: APPROVED` via API); desktop-app alerts confirmed arriving organically.
- Closed the Development-vs-Live question empirically: dev-mode app delivered an approved template to a no-role recipient (+521 33 2938 1425, invite still pending). Live mode only needed for future inbound webhooks.
- Corrected `cushlabs-whatsapp/docs/WHATSAPP_SETUP.md` §8 + troubleshooting (unpublished-app delivery claim disproven; "accepted but not delivered" = free-form outside 24h window).
- Added 12-lesson "WhatsApp Twilio→Meta Migration (July 2026)" section to `docs/LESSONS_LEARNED.md`.

### Decisions Made

- App stays in Development mode permanently for own-WABA outbound use: the Live toggle gates public OAuth/webhooks, not server-to-server sending.
- Future CushLabs products: reuse number + WABA + app, but one System User per product (blast-radius isolation for token rotation).
- Token values must never touch watched files during a session — paste into Vercel dashboard / edit `.env.local` only outside active sessions.

### Immediate Next Steps

- [ ] Retry "Rank It Better" WABA deletion after Twilio's billing cycle settles the BSP-era balance (early August).
- [ ] Check WhatsApp Manager → number → Automations tab for a no-code away-message ("replies not monitored") before real users onboard.
- [ ] Add a "replies aren't monitored" line to `whatsapp_optin` next time templates are revised (edit triggers re-review).

### Technical Debt

- No inbound webhook: replies/button-taps (incl. opt-in buttons) go unheard; delivery-failure callbacks invisible. Required before real users.
- Old expired Quickstart token still sits on line 1 of `backend/.env.local` (`WHATSAPP_TOKEN`) — harmless, delete anytime.

### Open Questions / Blockers

- cushlabs-investment-model auth failure + Cloudflare token re-wiring — with the parallel agent (not this repo's stack).

---

## Session: 2026-07-14

### Accomplished

- Completed the Twilio→Meta WhatsApp migration end-to-end: production template send verified via `https://stockalert-api.vercel.app/api/send_whatsapp` (HTTP 200, delivered to real phone). PR #18 squash-merged.
- Root-caused the persistent `#200` send-permission error: the BSP-era "Rank It Better" WABA was unusable for direct Cloud API sends. Created fresh WABA **CushLabs Notifications** (`1669695934130784`), moved +1 307-284-2785 in (new Phone Number ID `1203172156219078`), voice-verified, registered, subscribed the app — all via Graph API.
- Both templates APPROVED on the new WABA: `stock_price_alert` (UTILITY), `whatsapp_optin` (MARKETING, auto-recategorized).
- Vercel prod env swapped (`WHATSAPP_*` in, `TWILIO_*` removed) and redeployed twice (second deploy picked up `KV_REST_API_*` rate-limit naming from main).
- Deleted the Twilio WhatsApp Sender; archived 4 dead Meta apps; renamed "NY English Page Assistant" → "CushLabs Page Assistant"; updated `operating-system` registry docs (meta-apps-map, whatsapp-infrastructure).

### Decisions Made

- Fresh WABA over Meta Support ticket: identical token sent instantly via non-BSP WABAs but always failed on the BSP-era one — self-serve fix beat an unbounded support queue.
- Display name "CushLabs" (not per-product): shared-number strategy; templates self-identify ("StockAlert Price Alert: ...").
- App stays in Development mode: own-WABA sending needs only Standard Access — no App Review, no publish.

### Immediate Next Steps

- [ ] Delete the retired "Rank It Better" WABA (`1532215101406482`) in Business Settings → WhatsApp accounts (Robert, ~1 min — safe now).
- [ ] Verify display name "CushLabs" cleared review (WhatsApp Manager → Phone numbers → status next to +1 307-284-2785).
- [ ] Desktop-app smoke test: toggle "Enable WhatsApp" in StockAlert and confirm the opt-in + a live alert arrive (contract unchanged; not re-tested post-migration).

### Technical Debt

- `whatsapp_optin` runs as MARKETING (pricier per conversation, stricter pacing) — consider rewording and resubmitting as UTILITY someday.
- No webhook endpoint: async delivery failures (e.g. free-form outside 24h window) are invisible; fine for solo use, needed before real users.

### Open Questions / Blockers

- None.

---
