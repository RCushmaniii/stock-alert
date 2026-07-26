/**
 * US equity market hours, evaluated in the exchange's own timezone.
 *
 * Everything here is derived from `Intl.DateTimeFormat` with an explicit
 * timeZone, so daylight saving is handled by the runtime rather than by
 * hand-rolled offset math (a recurring source of "alerts fired an hour late
 * in November" bugs).
 */

export interface MarketStatus {
  open: boolean;
  /** Human-readable explanation, recorded in run_log for observability. */
  reason: string;
  /** Exchange-local date, YYYY-MM-DD. */
  date: string;
  /** Exchange-local time, HH:MM (24h). */
  time: string;
}

const OPEN_MINUTES = 9 * 60 + 30; // 09:30 ET
const CLOSE_MINUTES = 16 * 60; // 16:00 ET
const EARLY_CLOSE_MINUTES = 13 * 60; // 13:00 ET

/** NYSE/Nasdaq full-day closures. */
const HOLIDAYS = new Set<string>([
  // 2026
  "2026-01-01", // New Year's Day
  "2026-01-19", // MLK Jr. Day
  "2026-02-16", // Presidents' Day
  "2026-04-03", // Good Friday
  "2026-05-25", // Memorial Day
  "2026-06-19", // Juneteenth
  "2026-07-03", // Independence Day (observed, Jul 4 falls on Saturday)
  "2026-09-07", // Labor Day
  "2026-11-26", // Thanksgiving
  "2026-12-25", // Christmas
  // 2027 - listed ahead of time so the monitor does not silently trade
  // through a holiday the moment the year rolls over.
  "2027-01-01",
  "2027-01-18",
  "2027-02-15",
  "2027-03-26",
  "2027-05-31",
  "2027-06-18", // Juneteenth observed (Jun 19 is a Saturday)
  "2027-07-05", // Independence Day observed (Jul 4 is a Sunday)
  "2027-09-06",
  "2027-11-25",
  "2027-12-24", // Christmas observed (Dec 25 is a Saturday)
]);

/** Half days - market closes at 13:00 ET. */
const EARLY_CLOSES = new Set<string>([
  "2026-11-27", // day after Thanksgiving
  "2026-12-24", // Christmas Eve
  "2027-11-26",
]);

/**
 * Determine whether the US equity market is currently open.
 *
 * @param now Instant to evaluate (UTC-based Date).
 * @param timeZone IANA timezone of the exchange.
 */
export function marketStatus(now: Date, timeZone: string): MarketStatus {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    weekday: "short",
  });

  const parts: Record<string, string> = {};
  for (const part of formatter.formatToParts(now)) {
    parts[part.type] = part.value;
  }

  const date = `${parts.year}-${parts.month}-${parts.day}`;
  // Some ICU builds emit hour "24" for midnight under hour12:false.
  const hour = Number(parts.hour) % 24;
  const minute = Number(parts.minute);
  const time = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  const minutes = hour * 60 + minute;
  const weekday = parts.weekday ?? "";

  if (weekday === "Sat" || weekday === "Sun") {
    return { open: false, reason: `weekend (${weekday})`, date, time };
  }
  if (HOLIDAYS.has(date)) {
    return { open: false, reason: "market holiday", date, time };
  }
  if (minutes < OPEN_MINUTES) {
    return { open: false, reason: "pre-market", date, time };
  }

  const closeAt = EARLY_CLOSES.has(date) ? EARLY_CLOSE_MINUTES : CLOSE_MINUTES;
  if (minutes >= closeAt) {
    return {
      open: false,
      reason: EARLY_CLOSES.has(date) ? "after early close" : "after close",
      date,
      time,
    };
  }

  return { open: true, reason: "open", date, time };
}
