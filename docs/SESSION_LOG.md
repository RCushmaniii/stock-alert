# Session Log — ai-stock-alert

Entries are newest-first. Each entry documents one Claude Code working session.

---

<!-- New entries go above this line -->

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
