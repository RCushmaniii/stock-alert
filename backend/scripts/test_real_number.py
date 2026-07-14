"""One-time verification: send via the REAL number (+13072842785, Rank It
Better WABA) using the long-lived System User token, via an already-APPROVED
legacy template (migrated from the old Twilio Content Template) rather than
our new stock_price_alert/whatsapp_optin templates, which are still PENDING
review. Proves the real number + long-lived token work end-to-end.

Run from the backend/ directory:

    python scripts/test_real_number.py +1XXXXXXXXXX

Reads credentials from backend/.env.local (gitignored). Prefers
WHATSAPP_TOKEN_SYS_USER (the long-lived token) over WHATSAPP_TOKEN (the
temporary Quickstart one) if both are present. Never logs the token.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(".env.local", override=True)

REAL_PHONE_NUMBER_ID = "877346822138630"  # +13072842785, Rank It Better WABA
LEGACY_APPROVED_TEMPLATE = "ai_stock_price_alert_02_hx138b713346901520a4a6d48e21ec3e68"


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_real_number.py +1XXXXXXXXXX")
        raise SystemExit(1)

    to_number = sys.argv[1].lstrip("+")
    token = os.environ.get("WHATSAPP_TOKEN_SYS_USER") or os.environ.get("WHATSAPP_TOKEN")
    api_version = os.environ.get("GRAPH_API_VERSION", "v25.0")

    if not token or "PASTE_YOUR" in token:
        print("No usable token found (WHATSAPP_TOKEN_SYS_USER or WHATSAPP_TOKEN) in .env.local")
        raise SystemExit(1)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {
            "name": LEGACY_APPROVED_TEMPLATE,
            "language": {"code": "en_US"},
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

    url = f"https://graph.facebook.com/{api_version}/{REAL_PHONE_NUMBER_ID}/messages"
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
            print("SUCCESS:")
            print(json.dumps(body, indent=2))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        print("ERROR:")
        print(raw)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
