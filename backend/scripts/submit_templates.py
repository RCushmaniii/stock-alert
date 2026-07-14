"""Submit StockAlert's WhatsApp message templates to Meta for review.

Run once WHATSAPP_TOKEN and WHATSAPP_WABA_ID exist (Phase 0 of the Twilio->
Meta migration is complete), from the backend/ directory:

    python scripts/submit_templates.py

Reads credentials from backend/.env.local (gitignored). Never logs the token.
Prints only template name + submission status/id.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv
from whatsapp_templates import ALL_TEMPLATES

load_dotenv(".env.local", override=True)


def submit_template(waba_id: str, token: str, template: dict, api_version: str) -> None:
    url = f"https://graph.facebook.com/{api_version}/{waba_id}/message_templates"
    data = json.dumps(template).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            print(f"  SUBMITTED: {template['name']} -> id={body.get('id')} status={body.get('status', 'PENDING')}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        error = json.loads(raw).get("error", {}) if raw else {}
        print(f"  ERROR submitting {template['name']}:")
        print(f"    message: {error.get('message')}")
        print(f"    error_user_title: {error.get('error_user_title')}")
        print(f"    error_user_msg: {error.get('error_user_msg')}")
        print(f"    error_data: {error.get('error_data')}")


def main() -> None:
    token = os.environ.get("WHATSAPP_TOKEN")
    waba_id = os.environ.get("WHATSAPP_WABA_ID")

    if not token or not waba_id:
        print("Missing WHATSAPP_TOKEN or WHATSAPP_WABA_ID in environment.")
        raise SystemExit(1)

    api_version = os.environ.get("GRAPH_API_VERSION", "v21.0")
    print(f"Submitting {len(ALL_TEMPLATES)} template(s) to WABA {waba_id} ({api_version})...")
    for template in ALL_TEMPLATES:
        submit_template(waba_id, token, template, api_version)


if __name__ == "__main__":
    main()
