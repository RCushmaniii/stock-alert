"""Check review status of StockAlert's Meta WhatsApp message templates.

Run from the backend/ directory:

    python scripts/template_status.py

Reads credentials from backend/.env.local (gitignored). Never logs the token.
Prints only template name/status.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv
from whatsapp_templates import ALL_TEMPLATES

load_dotenv(".env.local", override=True)


def main() -> None:
    token = os.environ.get("WHATSAPP_TOKEN_SYS_USER") or os.environ.get("WHATSAPP_TOKEN")
    waba_id = os.environ.get("WHATSAPP_WABA_ID")

    if not token or not waba_id:
        print("Missing WHATSAPP_TOKEN or WHATSAPP_WABA_ID in environment.")
        raise SystemExit(1)

    api_version = os.environ.get("GRAPH_API_VERSION", "v21.0")
    # The Graph API's `name` filter on this endpoint matches a single exact
    # name, not a comma-separated list (a comma-joined value silently
    # matches nothing) - fetch all templates and filter client-side instead.
    wanted_names = {t["name"] for t in ALL_TEMPLATES}
    query = urllib.parse.urlencode({"fields": "name,status,category,language", "limit": 100})
    url = f"https://graph.facebook.com/{api_version}/{waba_id}/message_templates?{query}"
    request = urllib.request.Request(url, method="GET")
    request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
            found = {item.get("name") for item in body.get("data", [])}
            for item in body.get("data", []):
                if item.get("name") in wanted_names:
                    print(f"  {item.get('name')}: {item.get('status')} ({item.get('category')}, {item.get('language')})")
            for missing in wanted_names - found:
                print(f"  {missing}: NOT SUBMITTED")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        error = json.loads(raw).get("error", {}) if raw else {}
        print(f"ERROR: {error.get('message', raw[:200])}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
