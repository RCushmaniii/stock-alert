-- StockAlert cloud monitor schema (Cloudflare D1).
--
-- Multi-user from day one: every row carries a user_id, and the WhatsApp
-- recipient lives in the `users` table rather than an env var. This follows
-- the CushLabs rule that no global/env var may hold a tenant-specific value -
-- adding user #2 is an INSERT, not a refactor.

CREATE TABLE IF NOT EXISTS users (
  id              TEXT PRIMARY KEY,
  display_name    TEXT,
  whatsapp_phone  TEXT NOT NULL,          -- E.164, no leading '+'
  locale          TEXT NOT NULL DEFAULT 'en',
  enabled         INTEGER NOT NULL DEFAULT 1,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS watches (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id         TEXT NOT NULL,
  symbol          TEXT NOT NULL,
  name            TEXT,
  low_threshold   REAL,
  high_threshold  REAL,
  enabled         INTEGER NOT NULL DEFAULT 1,
  created_at      TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE (user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_watches_user ON watches (user_id, enabled);

-- One row per (user, symbol). `zone` records which band the price was in on
-- the last check: 'high' (>= high_threshold), 'low' (<= low_threshold) or
-- 'none' (inside the band). An alert fires only on a zone TRANSITION into
-- high/low, so a stock that sits above its threshold all day alerts once,
-- not every 5 minutes.
CREATE TABLE IF NOT EXISTS alert_state (
  user_id         TEXT NOT NULL,
  symbol          TEXT NOT NULL,
  zone            TEXT NOT NULL DEFAULT 'none',
  last_price      REAL,
  last_alert_at   TEXT,
  updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (user_id, symbol)
);

CREATE TABLE IF NOT EXISTS alert_log (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id         TEXT NOT NULL,
  symbol          TEXT NOT NULL,
  price           REAL NOT NULL,
  threshold       REAL NOT NULL,
  direction       TEXT NOT NULL,          -- 'above' | 'below'
  status          TEXT NOT NULL,          -- 'sent' | 'failed'
  wamid           TEXT,
  error_code      TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_alert_log_created ON alert_log (created_at DESC);

CREATE TABLE IF NOT EXISTS run_log (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  market_open     INTEGER NOT NULL,
  reason          TEXT,
  checked         INTEGER NOT NULL DEFAULT 0,
  alerts_sent     INTEGER NOT NULL DEFAULT 0,
  errors          INTEGER NOT NULL DEFAULT 0,
  duration_ms     INTEGER,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_run_log_created ON run_log (created_at DESC);
