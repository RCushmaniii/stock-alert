"""One-time verification: send Meta's default hello_world template via the
Graph API, using the Test WhatsApp Business Account (auto-approved template,
no submission needed). Proves token/phone-number-id/network/auth all work
before wiring up production templates on the real number.

Run from the backend/ directory:

    python scripts/test_hello_world.py +1XXXXXXXXXX

Reads credentials from backend/.env.local (gitignored). Never logs the token.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv(".env.local", override=True)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_hello_world.py +1XXXXXXXXXX")
        raise SystemExit(1)

    to_number = sys.argv[1].lstrip("+")
    token = os.environ.get("WHATSAPP_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    api_version = os.environ.get("GRAPH_API_VERSION", "v25.0")

    if not token or not phone_number_id or "PASTE_YOUR" in token:
        print("WHATSAPP_TOKEN or WHATSAPP_PHONE_NUMBER_ID missing/unset in .env.local")
        raise SystemExit(1)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
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
