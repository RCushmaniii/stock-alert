"""Send one real WhatsApp message through the production sender.

Manual verification tool - NOT a pytest test despite the filename (it defines
no test_* functions, so collection is a no-op).

Run from the backend/ directory:

    python scripts/test_real_number.py +1XXXXXXXXXX

Reads credentials from backend/.env.local (gitignored). Prefers
WHATSAPP_TOKEN_SYS_USER (the long-lived System User token) over WHATSAPP_TOKEN.
Never logs the token, and never prints the Graph API `error.message`, which can
echo the access token back on malformed-token errors.

History: this script previously hardcoded phone number id 877346822138630 and a
legacy Twilio-migrated template, both belonging to the retired "Rank It Better"
WABA. Those were dead after the 2026-07-14 move to the "CushLabs Notifications"
WABA. It now reads the phone number id from the environment, so it can never
drift from production again.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(".env.local", override=True)

TEMPLATE_NAME = "stock_price_alert"
TEMPLATE_LANGUAGE = "en_US"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_real_number.py +1XXXXXXXXXX")
        raise SystemExit(1)

    to_number = sys.argv[1].lstrip("+")
    token = os.environ.get("WHATSAPP_TOKEN_SYS_USER") or os.environ.get("WHATSAPP_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    api_version = os.environ.get("GRAPH_API_VERSION", "v25.0")

    if not token or "PASTE_YOUR" in token:
        print("No usable token found (WHATSAPP_TOKEN_SYS_USER or WHATSAPP_TOKEN) in .env.local")
        raise SystemExit(1)

    if not phone_number_id:
        print("WHATSAPP_PHONE_NUMBER_ID not set in .env.local")
        raise SystemExit(1)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": TEMPLATE_NAME,
            "language": {"code": TEMPLATE_LANGUAGE},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "AAPL"},
                        {"type": "text", "text": "182.50"},
                        {"type": "text", "text": "above"},
                        {"type": "text", "text": "180.00"},
                    ],
                }
            ],
        },
    }

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            messages = body.get("messages", [{}])
            print("SENT OK")
            print(f"  message_id: {messages[0].get('id', 'n/a')}")
            print(f"  to (masked): ...{to_number[-4:]}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        error = json.loads(raw).get("error", {}) if raw else {}
        # Deliberately NOT printing error.message - it can contain the token.
        print("SEND FAILED")
        print(f"  http: {exc.code}")
        print(f"  code: {error.get('code')} subcode: {error.get('error_subcode')}")
        print(f"  type: {error.get('type')}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
