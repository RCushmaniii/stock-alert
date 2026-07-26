/**
 * Finnhub quote client.
 *
 * The API key travels in the query string, so the request URL is NEVER logged.
 * Only the symbol and HTTP status appear in logs.
 *
 * Transient failures are retried. A dropped quote means a missed price
 * crossing, and a missed crossing is the exact failure this product exists to
 * prevent - so a blip must not cost an alert. Observed 2026-07-25: a single
 * run returned 6/8 failures from Cloudflare egress and was never reproducible
 * across ~40 subsequent calls, so the cause is treated as transient rather
 * than guessed at.
 */

export interface Quote {
  /** Current price. */
  current: number;
  /** Previous close. */
  previousClose: number;
  /** Day high. */
  dayHigh: number;
  /** Day low. */
  dayLow: number;
}

interface FinnhubQuoteResponse {
  c?: number;
  pc?: number;
  h?: number;
  l?: number;
}

interface Attempt {
  quote: Quote | null;
  /** Whether retrying could plausibly succeed. */
  retryable: boolean;
  /** Short, secret-free description for logs. */
  detail: string;
}

const MAX_ATTEMPTS = 3;
/** Backoff before attempt 2 and attempt 3. */
const RETRY_DELAYS_MS = [250, 750];

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function attemptQuote(symbol: string, apiKey: string): Promise<Attempt> {
  const url =
    `https://finnhub.io/api/v1/quote?symbol=${encodeURIComponent(symbol)}` +
    `&token=${encodeURIComponent(apiKey)}`;

  let response: Response;
  try {
    response = await fetch(url, {
      headers: { "User-Agent": "CushLabs-StockAlert/1.0" },
    });
  } catch (error) {
    return {
      quote: null,
      retryable: true,
      detail: `network: ${(error as Error).message}`,
    };
  }

  if (!response.ok) {
    // 429 = rate limited, 5xx = upstream blip. Both worth retrying.
    // 401/403 (bad key) and 404 (unknown symbol) will never succeed on retry.
    const retryable = response.status === 429 || response.status >= 500;
    return { quote: null, retryable, detail: `HTTP ${response.status}` };
  }

  let data: FinnhubQuoteResponse;
  try {
    data = (await response.json()) as FinnhubQuoteResponse;
  } catch {
    return { quote: null, retryable: true, detail: "malformed JSON" };
  }

  // Finnhub uses a zero price as its "no data" sentinel.
  if (typeof data.c !== "number" || data.c === 0) {
    return { quote: null, retryable: false, detail: "no price in response" };
  }

  return {
    quote: {
      current: data.c,
      previousClose: typeof data.pc === "number" ? data.pc : 0,
      dayHigh: typeof data.h === "number" ? data.h : 0,
      dayLow: typeof data.l === "number" ? data.l : 0,
    },
    retryable: false,
    detail: "ok",
  };
}

/**
 * Fetch the current quote for a symbol, retrying transient failures.
 *
 * @returns The quote, or null when every attempt failed or the symbol has no
 *          usable price.
 */
export async function getQuote(
  symbol: string,
  apiKey: string,
): Promise<Quote | null> {
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    const result = await attemptQuote(symbol, apiKey);

    if (result.quote !== null) {
      if (attempt > 1) {
        console.log(`finnhub: ${symbol} recovered on attempt ${attempt}`);
      }
      return result.quote;
    }

    if (!result.retryable || attempt === MAX_ATTEMPTS) {
      console.error(
        `finnhub: ${symbol} failed (${result.detail}) after ${attempt} attempt(s)`,
      );
      return null;
    }

    await sleep(RETRY_DELAYS_MS[attempt - 1]);
  }

  return null;
}
