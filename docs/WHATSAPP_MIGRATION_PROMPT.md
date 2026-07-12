# Prompt — Migrate WhatsApp from Twilio to Meta Cloud API

> Paste the block below into a fresh Claude Code session **in the `ai-stock-alert`
> repo**. It is self-contained. Prerequisites that only Robert can do (Meta app +
> number registration) are called out as blockers — the assistant should build the
> code against them and stop where it genuinely needs them.

---

```
You are working in the ai-stock-alert repo. Goal: migrate the app's WhatsApp
sending OFF Twilio and onto Meta's WhatsApp Cloud API (Graph API) directly.

HARD CONSTRAINT ON SCOPE:
- We are keeping Twilio for ONE thing only: buying/hosting the phone number.
- Everything else WhatsApp — sending messages, creating and managing message
  templates, the WABA — moves to Meta's WhatsApp Cloud API, called directly.
- Do NOT introduce any new Twilio WhatsApp features. Remove Twilio from the
  message-sending path entirely.

CURRENT STATE (what exists today):
- Sending lives in backend/api/send_whatsapp.py — a Vercel Python serverless
  handler that uses `from twilio.rest import Client`.
- Env today: TWILIO_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER (+1 307 284 2785),
  API_KEY (auth on the endpoint).
- Two Twilio Content Templates are in use:
  * Stock alert  — vars {{1}}=symbol, {{2}}=price, {{3}}=direction, {{4}}=threshold.
  * Opt-in       — var  {{1}}=stock_count.
- There is country-aware E.164 phone formatting (Mexico needs the +521 mobile
  prefix, Argentina +549, etc.). KEEP this formatting logic exactly — it is
  correct and hard-won.
- The desktop app (PyQt6) POSTs to this endpoint with an X-API-Key header and a
  JSON body like { phone, country_code, template_data, template_type }. Preserve
  this request/response contract, or update BOTH sides in the same change.

TARGET ARCHITECTURE (Meta WhatsApp Cloud API, direct):
- Send with: POST https://graph.facebook.com/v{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages
  Authorization: Bearer {WHATSAPP_TOKEN}
  Body: WhatsApp "template" messages for business-initiated alerts (that's all of
  them), with components/parameters mapping the same variables as today.
- Recreate BOTH templates as Meta WhatsApp message templates, category UTILITY,
  and submit them for approval (via WhatsApp Manager or the Graph
  /{WABA_ID}/message_templates endpoint). Map the variables 1:1 with the current
  Twilio templates. Alerts are ALWAYS templates (business-initiated, likely
  outside the 24h window); free-form text is only valid inside a 24h user-initiated
  session — don't rely on it for alerts.
- New environment variables (replace the Twilio message vars):
    WHATSAPP_TOKEN            (System User never-expiry token; scopes
                               whatsapp_business_messaging + whatsapp_business_management)
    WHATSAPP_PHONE_NUMBER_ID  (Meta-issued; NOT the raw phone number)
    WHATSAPP_WABA_ID
    GRAPH_API_VERSION         (e.g. v21.0)
  Keep API_KEY (endpoint auth). Remove TWILIO_SID / TWILIO_AUTH_TOKEN /
  TWILIO_WHATSAPP_NUMBER from the sending path and from .env.example. Update
  backend/requirements.txt (drop the twilio dependency; you need only stdlib +
  an HTTP call — use urllib or httpx, no SDK required).

REFERENCE IMPLEMENTATION:
- The sibling repo ../cushlabs-whatsapp is a proven, LIVE Meta WhatsApp Cloud API
  integration. Mirror its Send API call shape, template payload structure, Graph
  API version handling, and error handling. Read
  ../cushlabs-whatsapp/docs/WHATSAPP_SETUP.md and its src/whatsapp.ts first.

SECRETS / SAFETY (non-negotiable):
- Never print, log, or echo WHATSAPP_TOKEN (a long "EAA..." token) or any secret.
- Meta's Graph API can echo the access token back inside error.message on a
  "malformed token" error — this caused a real leak in v1. Sanitize/strip any
  Graph error before logging; never surface error.message verbatim to the client.
- Keep all secrets in env / .env.local (gitignored). Update .env.example with
  KEY NAMES ONLY (no values).

BLOCKERS — build up to these, then STOP and report; do not fake them:
1. Meta app + WABA: this repo needs a WhatsApp Business Account and a Meta app to
   send from. Robert must decide/provide: either a dedicated new Meta app + WABA
   for ai-stock-alert, or onboard this number as a tenant of the CushLabs Connect
   platform. Everything lives under the CushLabs business portfolio (727942370887684).
2. Phone number registration: the Twilio number (or a new one) must be registered
   INTO that WABA and verified via its SMS/voice code. WARNING: verifying a
   VoIP/Twilio number with Meta is historically painful — the number must be able
   to receive the verification code in the Twilio console; not all number types
   work. Flag this clearly; don't assume it "just works".
3. Template approval: templates must be APPROVED by Meta before they can send.
   Build and submit them, then note that sending can't be verified until approval.

DELIVERABLES:
- Rewritten backend/api/send_whatsapp.py using Meta Cloud API (Twilio removed from
  the send path), preserving the endpoint's request/response contract and the
  phone-formatting logic.
- Template definitions/payloads for the two templates (ready to submit), variable
  mapping documented.
- Updated .env.example, backend/requirements.txt, and any backend/README notes.
- A short MIGRATION section in the repo docs describing what changed, the new env
  vars, and the manual steps (app/WABA, number registration, template approval).
- A test path: a way to send a test alert to Robert's number once creds + approval
  are in place.

Start by reading the current send_whatsapp.py and the cushlabs-whatsapp reference,
then propose the plan before making changes.
```

---

## Notes for Robert (not part of the prompt)

- **The one real decision this surfaces:** does ai-stock-alert get its **own Meta
  app + WABA**, or become a **tenant of CushLabs Connect** once Connect is
  approved? Connect is the long-term home for all CushLabs WhatsApp, so onboarding
  it as a tenant is the cleaner end-state — but that's gated on Connect's App
  Review. A dedicated app unblocks you now. Your call; the prompt is written to
  work either way.
- **VoIP verification is the likely time-sink**, per v1's lessons — the code change
  is the easy part.
- See `operating-system/cushlabs/whatsapp-infrastructure.md` for the full context.
