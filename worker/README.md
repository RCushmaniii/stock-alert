# StockAlert Cloud Monitor

A Cloudflare Worker that watches stock prices **24/7 and sends WhatsApp alerts**,
independent of whether the Windows desktop app (or the PC it runs on) is awake.

Live: `https://stockalert-monitor.rcushmaniii.workers.dev`

## Why this exists

The desktop app's polling loop only runs while the PC is on. That makes the
alert useless in exactly the situation it matters most — away from the machine,
needing to act on a price move. This Worker moves the _monitoring_ to the cloud;
WhatsApp is the delivery surface, so no mobile app is needed.

## How it works

```
Cron (*/5) → market-hours gate → Finnhub quotes → zone transition?
           → WhatsApp Cloud API (CushLabs WABA) → D1 alert_log
```

- **Market-hours gate** — outside 09:30–16:00 ET Mon–Fri (holidays and half
  days included), the Worker exits immediately and makes **zero** Finnhub calls.
- **Zone transitions, not levels** — an alert fires when a price _crosses into_
  its high or low band. A stock sitting above its threshold all afternoon sends
  **one** message, not one every five minutes. Returning inside the band re-arms it.
- **Retries** — transient Finnhub failures retry up to 3 times with backoff. A
  dropped quote would mean a missed crossing.
- **Sender** — CushLabs Notifications WABA, `stock_price_alert` template
  (approved UTILITY), from +1 307 284 2785.

## Multi-user by construction

Every table carries `user_id`, and the WhatsApp recipient lives in the `users`
table — **not** an env var. This follows the CushLabs rule that no global may
hold a tenant-specific value. Adding a second user is an `INSERT`, not a refactor.

## Commands

```powershell
pnpm deploy        # deploy to Cloudflare
pnpm typecheck     # tsc --noEmit
pnpm tail          # live logs
pnpm db:schema     # apply schema.sql to remote D1
```

## Endpoints

| Endpoint              | Auth          | Purpose                                         |
| --------------------- | ------------- | ----------------------------------------------- |
| `GET /health`         | none          | Market status, counts, last run                 |
| `POST /check?force=1` | `X-Admin-Key` | Run a pass now (`force=1` ignores market hours) |
| `GET /alerts`         | `X-Admin-Key` | Last 25 alerts sent                             |
| `GET /runs`           | `X-Admin-Key` | Last 25 monitor runs                            |
| `GET /state`          | `X-Admin-Key` | Current thresholds and band state per symbol    |

## Secrets

Set via `wrangler secret bulk .dev.vars` (never per-key `secret put` in a loop —
stdin piping fails silently in non-TTY contexts).

`FINNHUB_API_KEY` · `WHATSAPP_TOKEN` · `WHATSAPP_PHONE_NUMBER_ID` · `ADMIN_KEY`

## Known gaps

- **No Sentry yet.** CushLabs standard requires error monitoring on production
  services. Observability is currently `run_log` + `wrangler tail` only.
- **No rate limiting on the admin endpoints** beyond the shared `ADMIN_KEY`.
- **Holidays are hardcoded** through 2027 in `src/market-hours.ts` — extend before then.
