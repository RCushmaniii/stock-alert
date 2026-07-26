/**
 * WhatsApp Cloud API sender (Meta Graph API, direct).
 *
 * SECURITY: Graph API error responses can echo the access token back inside
 * `error.message` on malformed-token errors - this caused a real credential
 * leak in an earlier CushLabs WhatsApp project. We therefore log and persist
 * only `error.code` / `error.type`, never `error.message`.
 */

import type { Env } from "./types";

/** Meta template name, approved as UTILITY on the CushLabs Notifications WABA. */
export const PRICE_ALERT_TEMPLATE = "stock_price_alert";
const TEMPLATE_LANGUAGE = "en_US";

export interface SendResult {
  ok: boolean;
  /** Meta message id (wamid...) on success. */
  wamid?: string;
  /** Graph API error code, safe to log. */
  errorCode?: string;
}

interface GraphSendResponse {
  messages?: Array<{ id?: string }>;
  error?: { code?: number; type?: string; error_subcode?: number };
}

/**
 * Send a price-alert template message.
 *
 * Template body: "{{1}} is now trading at ${{2}} per share, which is {{3}} the
 * alert threshold of ${{4}} you set in the StockAlert app."
 *
 * @param to Recipient in E.164 without the leading '+'.
 * @param direction "above" or "below".
 */
export async function sendPriceAlert(
  env: Env,
  to: string,
  symbol: string,
  price: number,
  direction: "above" | "below",
  threshold: number,
): Promise<SendResult> {
  const payload = {
    messaging_product: "whatsapp",
    to,
    type: "template",
    template: {
      name: PRICE_ALERT_TEMPLATE,
      language: { code: TEMPLATE_LANGUAGE },
      components: [
        {
          type: "body",
          parameters: [
            { type: "text", text: symbol },
            { type: "text", text: price.toFixed(2) },
            { type: "text", text: direction },
            { type: "text", text: threshold.toFixed(2) },
          ],
        },
      ],
    },
  };

  const url =
    `https://graph.facebook.com/${env.GRAPH_API_VERSION}` +
    `/${env.WHATSAPP_PHONE_NUMBER_ID}/messages`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.WHATSAPP_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    console.error(
      `whatsapp: ${symbol} network error: ${(error as Error).message}`,
    );
    return { ok: false, errorCode: "network" };
  }

  const body = (await response.json().catch(() => ({}))) as GraphSendResponse;

  if (!response.ok) {
    const code = body.error?.code ?? response.status;
    const subcode = body.error?.error_subcode;
    // Deliberately NOT logging error.message - it can contain the token.
    console.error(
      `whatsapp: ${symbol} send failed http=${response.status} code=${code}` +
        (subcode ? ` subcode=${subcode}` : ""),
    );
    return { ok: false, errorCode: String(code) };
  }

  const wamid = body.messages?.[0]?.id;
  return wamid ? { ok: true, wamid } : { ok: true };
}
