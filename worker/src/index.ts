/**
 * StockAlert cloud monitor - Cloudflare Worker.
 *
 * Runs on a cron trigger every 5 minutes. During US market hours it fetches a
 * quote for every enabled watch, and sends a WhatsApp alert when a price
 * TRANSITIONS into its high or low band. Alerts fire once per crossing: a
 * stock that sits above its threshold all afternoon produces one message, not
 * one every cycle. The state resets when the price returns inside the band.
 *
 * This replaces the polling loop that previously lived inside the Windows
 * desktop app, so alerts no longer depend on a PC being awake.
 */

import { getQuote } from "./finnhub";
import { marketStatus } from "./market-hours";
import type { Env, RunSummary, User, Watch, Zone } from "./types";
import { sendPriceAlert } from "./whatsapp";

/** Decide which band a price falls into. */
function classifyZone(
  price: number,
  low: number | null,
  high: number | null,
): Zone {
  if (high !== null && price >= high) return "high";
  if (low !== null && price <= low) return "low";
  return "none";
}

/** Persist the per-symbol band state, creating the row when absent. */
async function upsertState(
  env: Env,
  userId: string,
  symbol: string,
  zone: Zone,
  price: number,
  alerted: boolean,
): Promise<void> {
  await env.DB.prepare(
    `INSERT INTO alert_state (user_id, symbol, zone, last_price, last_alert_at, updated_at)
     VALUES (?1, ?2, ?3, ?4, ?5, datetime('now'))
     ON CONFLICT(user_id, symbol) DO UPDATE SET
       zone = excluded.zone,
       last_price = excluded.last_price,
       last_alert_at = COALESCE(excluded.last_alert_at, alert_state.last_alert_at),
       updated_at = datetime('now')`,
  )
    .bind(
      userId,
      symbol,
      zone,
      price,
      alerted ? new Date().toISOString() : null,
    )
    .run();
}

/**
 * Execute one monitoring pass.
 *
 * @param force Run even when the market is closed (manual admin trigger).
 */
export async function runCheck(env: Env, force = false): Promise<RunSummary> {
  const startedAt = Date.now();
  const status = marketStatus(new Date(), env.MARKET_TZ);

  if (!status.open && !force) {
    const summary: RunSummary = {
      marketOpen: false,
      reason: status.reason,
      checked: 0,
      alertsSent: 0,
      errors: 0,
      durationMs: Date.now() - startedAt,
    };
    await recordRun(env, summary);
    return summary;
  }

  const users = await env.DB.prepare(
    "SELECT id, whatsapp_phone, locale FROM users WHERE enabled = 1",
  ).all<User>();

  let checked = 0;
  let alertsSent = 0;
  let errors = 0;

  for (const user of users.results) {
    const watches = await env.DB.prepare(
      `SELECT symbol, name, low_threshold, high_threshold
       FROM watches WHERE user_id = ?1 AND enabled = 1`,
    )
      .bind(user.id)
      .all<Watch>();

    if (watches.results.length === 0) continue;

    const states = await env.DB.prepare(
      "SELECT symbol, zone FROM alert_state WHERE user_id = ?1",
    )
      .bind(user.id)
      .all<{ symbol: string; zone: Zone }>();

    const previousZone = new Map<string, Zone>(
      states.results.map((row) => [row.symbol, row.zone]),
    );

    // 8 symbols per user is comfortably inside Finnhub's 60 calls/minute.
    const quotes = await Promise.all(
      watches.results.map(async (watch) => ({
        watch,
        quote: await getQuote(watch.symbol, env.FINNHUB_API_KEY),
      })),
    );

    for (const { watch, quote } of quotes) {
      if (quote === null) {
        errors += 1;
        continue;
      }
      checked += 1;

      const zone = classifyZone(
        quote.current,
        watch.low_threshold,
        watch.high_threshold,
      );
      const previous = previousZone.get(watch.symbol) ?? "none";

      // Only a transition INTO a band alerts. Staying in the band is silent,
      // and returning to 'none' re-arms the alert for the next crossing.
      const shouldAlert = zone !== "none" && zone !== previous;

      if (!shouldAlert) {
        await upsertState(
          env,
          user.id,
          watch.symbol,
          zone,
          quote.current,
          false,
        );
        continue;
      }

      const threshold =
        zone === "high"
          ? (watch.high_threshold ?? 0)
          : (watch.low_threshold ?? 0);
      const direction: "above" | "below" = zone === "high" ? "above" : "below";

      const result = await sendPriceAlert(
        env,
        user.whatsapp_phone,
        watch.symbol,
        quote.current,
        direction,
        threshold,
      );

      await env.DB.prepare(
        `INSERT INTO alert_log
           (user_id, symbol, price, threshold, direction, status, wamid, error_code)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)`,
      )
        .bind(
          user.id,
          watch.symbol,
          quote.current,
          threshold,
          direction,
          result.ok ? "sent" : "failed",
          result.wamid ?? null,
          result.errorCode ?? null,
        )
        .run();

      if (result.ok) {
        alertsSent += 1;
      } else {
        errors += 1;
      }

      // Record the new zone even on send failure, but leave the alert
      // un-stamped so a retry is possible on the next pass.
      await upsertState(
        env,
        user.id,
        watch.symbol,
        zone,
        quote.current,
        result.ok,
      );
    }
  }

  const summary: RunSummary = {
    marketOpen: status.open,
    reason: force && !status.open ? `forced (${status.reason})` : status.reason,
    checked,
    alertsSent,
    errors,
    durationMs: Date.now() - startedAt,
  };
  await recordRun(env, summary);
  return summary;
}

/** Append a row to run_log for observability. */
async function recordRun(env: Env, summary: RunSummary): Promise<void> {
  await env.DB.prepare(
    `INSERT INTO run_log (market_open, reason, checked, alerts_sent, errors, duration_ms)
     VALUES (?1, ?2, ?3, ?4, ?5, ?6)`,
  )
    .bind(
      summary.marketOpen ? 1 : 0,
      summary.reason,
      summary.checked,
      summary.alertsSent,
      summary.errors,
      summary.durationMs,
    )
    .run();
}

function json(data: unknown, statusCode = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status: statusCode,
    headers: { "Content-Type": "application/json" },
  });
}

function isAdmin(request: Request, env: Env): boolean {
  const provided = request.headers.get("X-Admin-Key");
  return Boolean(env.ADMIN_KEY) && provided === env.ADMIN_KEY;
}

export default {
  /** Cron entry point. */
  async scheduled(
    _event: ScheduledController,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<void> {
    ctx.waitUntil(
      runCheck(env).then((summary) => {
        console.log(
          `run: open=${summary.marketOpen} reason=${summary.reason} ` +
            `checked=${summary.checked} sent=${summary.alertsSent} ` +
            `errors=${summary.errors} ${summary.durationMs}ms`,
        );
      }),
    );
  },

  /** HTTP entry point - health check plus admin endpoints. */
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/health" || url.pathname === "/") {
      const status = marketStatus(new Date(), env.MARKET_TZ);
      const counts = await env.DB.prepare(
        `SELECT
           (SELECT COUNT(*) FROM users WHERE enabled = 1)   AS users,
           (SELECT COUNT(*) FROM watches WHERE enabled = 1) AS watches,
           (SELECT COUNT(*) FROM alert_log)                 AS alerts`,
      ).first<{ users: number; watches: number; alerts: number }>();

      const lastRun = await env.DB.prepare(
        "SELECT created_at, reason, checked, alerts_sent, errors FROM run_log ORDER BY id DESC LIMIT 1",
      ).first();

      return json({
        service: "stockalert-monitor",
        ok: true,
        market: status,
        counts,
        lastRun,
      });
    }

    if (url.pathname === "/check" && request.method === "POST") {
      if (!isAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const force = url.searchParams.get("force") === "1";
      return json(await runCheck(env, force));
    }

    if (url.pathname === "/alerts") {
      if (!isAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const rows = await env.DB.prepare(
        `SELECT symbol, price, threshold, direction, status, error_code, created_at
         FROM alert_log ORDER BY id DESC LIMIT 25`,
      ).all();
      return json(rows.results);
    }

    if (url.pathname === "/runs") {
      if (!isAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const rows = await env.DB.prepare(
        `SELECT market_open, reason, checked, alerts_sent, errors, duration_ms, created_at
         FROM run_log ORDER BY id DESC LIMIT 25`,
      ).all();
      return json(rows.results);
    }

    if (url.pathname === "/state") {
      if (!isAdmin(request, env)) return json({ error: "unauthorized" }, 401);
      const rows = await env.DB.prepare(
        `SELECT w.symbol, w.low_threshold, w.high_threshold,
                s.zone, s.last_price, s.last_alert_at, s.updated_at
         FROM watches w
         LEFT JOIN alert_state s ON s.user_id = w.user_id AND s.symbol = w.symbol
         WHERE w.enabled = 1
         ORDER BY w.symbol`,
      ).all();
      return json(rows.results);
    }

    return json({ error: "not found" }, 404);
  },
};
