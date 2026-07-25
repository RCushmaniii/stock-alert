/** Shared types for the StockAlert cloud monitor. */

export interface Env {
  DB: D1Database;

  /** Finnhub API key (secret). */
  FINNHUB_API_KEY: string;
  /** Meta System User token for the CushLabs WABA (secret). */
  WHATSAPP_TOKEN: string;
  /** Meta phone number id for the CushLabs sender (+1 307 284 2785). */
  WHATSAPP_PHONE_NUMBER_ID: string;
  /** Shared secret guarding the admin HTTP endpoints. */
  ADMIN_KEY: string;

  /** Pinned Graph API version, e.g. "v25.0". */
  GRAPH_API_VERSION: string;
  /** IANA timezone the market trades in, e.g. "America/New_York". */
  MARKET_TZ: string;
}

/** Which band the last observed price fell into. */
export type Zone = "high" | "low" | "none";

export interface User {
  id: string;
  whatsapp_phone: string;
  locale: string;
}

export interface Watch {
  symbol: string;
  name: string | null;
  low_threshold: number | null;
  high_threshold: number | null;
}

export interface RunSummary {
  marketOpen: boolean;
  reason: string;
  checked: number;
  alertsSent: number;
  errors: number;
  durationMs: number;
}
