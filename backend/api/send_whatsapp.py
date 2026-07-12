"""
StockAlert WhatsApp Notification API

Serverless function to send WhatsApp messages via Meta's WhatsApp Cloud API
(Graph API), called directly — no BSP/SDK in the send path. Deploy to Vercel.

Supports both:
- Template messages (for business-initiated alerts)
- Free-form messages (for user-initiated session replies)
"""

import json
import os
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler

# Meta WhatsApp message template names (must match APPROVED templates in
# WhatsApp Manager for the WABA identified by WHATSAPP_WABA_ID). Language
# code is fixed per template below; adjust once the real approved templates
# are confirmed.
STOCK_ALERT_TEMPLATE_NAME = "stock_price_alert"
STOCK_ALERT_TEMPLATE_LANGUAGE = "en_US"
OPTIN_TEMPLATE_NAME = "whatsapp_optin"
OPTIN_TEMPLATE_LANGUAGE = "en_US"

# Phone number formatting patterns by country
COUNTRY_FORMATS = {
    "1": {"name": "US/Canada", "length": 10},
    "52": {"name": "Mexico", "mobile_prefix": "1", "length": 10},
    "34": {"name": "Spain", "length": 9},
    "44": {"name": "UK", "length": 10},
    "54": {"name": "Argentina", "mobile_prefix": "9", "length": 10},
    "55": {"name": "Brazil", "length": 11},
    "56": {"name": "Chile", "length": 9},
    "57": {"name": "Colombia", "length": 10},
    "51": {"name": "Peru", "length": 9},
}


def format_phone_number(phone: str, country_code: str = None) -> str:
    """
    Format phone number to E.164 format for WhatsApp.

    Args:
        phone: Raw phone number input
        country_code: Optional country code (e.g., "1", "52", "34")

    Returns:
        Formatted phone number (e.g., +521XXXXXXXXXX for Mexico)
    """
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', phone)

    # If already has +, validate and return
    if cleaned.startswith('+'):
        # Check for Mexico mobile - needs the 1 after 52
        if cleaned.startswith('+52') and not cleaned.startswith('+521'):
            # Insert the 1 for mobile numbers
            if len(cleaned) == 13:  # +52 + 10 digits
                cleaned = '+521' + cleaned[3:]
        return cleaned

    # Remove leading zeros
    cleaned = cleaned.lstrip('0')

    # If country code provided, format accordingly
    if country_code:
        country_code = country_code.lstrip('+')

        # Handle Mexico special case - mobile numbers need 1 prefix
        if country_code == '52':
            # Remove 1 if already present at start, we'll add it
            if cleaned.startswith('1') and len(cleaned) == 11:
                cleaned = cleaned[1:]
            return f'+521{cleaned}'

        # Handle Argentina special case - mobile numbers need 9 prefix
        if country_code == '54':
            if cleaned.startswith('9'):
                cleaned = cleaned[1:]
            return f'+549{cleaned}'

        return f'+{country_code}{cleaned}'

    # Auto-detect based on length and patterns
    if len(cleaned) == 10:
        # Assume US/Canada
        return f'+1{cleaned}'
    elif len(cleaned) == 11 and cleaned.startswith('1'):
        # US/Canada with country code
        return f'+{cleaned}'
    elif len(cleaned) == 12 and cleaned.startswith('52'):
        # Mexico without mobile prefix
        return f'+521{cleaned[2:]}'
    elif len(cleaned) == 13 and cleaned.startswith('521'):
        # Mexico with mobile prefix
        return f'+{cleaned}'
    else:
        # Return as-is with + prefix
        return f'+{cleaned}'


def _sanitize_graph_error(error_body: dict) -> dict:
    """Strip anything from a Graph API error that could echo back the access token.

    Meta's Graph API has been observed echoing the raw access token inside
    error.message on "malformed token" errors. Never surface that verbatim.
    """
    error = error_body.get("error", {}) if isinstance(error_body, dict) else {}
    message = str(error.get("message", "Unknown error"))

    token = os.environ.get("WHATSAPP_TOKEN")
    if token:
        message = message.replace(token, "[REDACTED]")

    return {
        "code": error.get("code"),
        "type": error.get("type"),
        "error_subcode": error.get("error_subcode"),
        "message": message,
    }


def _graph_api_send(payload: dict) -> dict:
    """POST a message payload to the Meta WhatsApp Cloud API Send endpoint."""
    token = os.environ.get("WHATSAPP_TOKEN")
    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    api_version = os.environ.get("GRAPH_API_VERSION", "v21.0")

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
            return {"success": True, "body": body}
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8")
        error_body = json.loads(raw_body) if raw_body else {}
        return {"success": False, "error": _sanitize_graph_error(error_body)}
    except urllib.error.URLError as exc:
        return {"success": False, "error": {"message": f"Network error: {exc.reason}"}}


def send_whatsapp_message(to_number: str, message: str = None, template_data: dict = None, template_type: str = "alert") -> dict:
    """
    Send a WhatsApp message via Meta's WhatsApp Cloud API.

    Args:
        to_number: Recipient phone number (E.164 format, with leading +)
        message: Message text (for free-form/session messages)
        template_data: Dict with template variables
        template_type: "alert" for price alerts, "optin" for opt-in message

    Returns:
        dict with success status and message id or error
    """
    if not all([os.environ.get('WHATSAPP_TOKEN'), os.environ.get('WHATSAPP_PHONE_NUMBER_ID')]):
        return {
            'success': False,
            'error': 'WhatsApp credentials not configured'
        }

    # Meta's Send API expects the recipient number without the leading '+'
    to = to_number.lstrip('+')

    if template_data:
        if template_type == "optin":
            # Opt-in template: {{1}} = stock count
            body_params = [str(template_data.get("1") or template_data.get("stock_count", "0"))]
            template_name = OPTIN_TEMPLATE_NAME
            language_code = OPTIN_TEMPLATE_LANGUAGE
        else:
            # Alert template: {{1}}=symbol, {{2}}=price, {{3}}=direction, {{4}}=threshold
            body_params = [
                str(template_data.get("1") or template_data.get("symbol", "STOCK")),
                str(template_data.get("2") or template_data.get("price", "0.00")),
                str(template_data.get("3") or template_data.get("direction", "crossed")),
                str(template_data.get("4") or template_data.get("threshold", "0.00")),
            ]
            template_name = STOCK_ALERT_TEMPLATE_NAME
            language_code = STOCK_ALERT_TEMPLATE_LANGUAGE

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in body_params],
                    }
                ],
            },
        }
    else:
        # Free-form message (only works within 24hr session window)
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

    result = _graph_api_send(payload)

    if not result["success"]:
        error = result["error"]
        return {
            'success': False,
            'error': error.get('message', 'Unknown error'),
            'error_code': error.get('code'),
        }

    body = result["body"]
    messages = body.get("messages", [])
    message_id = messages[0]["id"] if messages else None

    return {
        'success': True,
        'message_sid': message_id,
        'status': 'accepted',
        'to': f'whatsapp:{to_number}',
        'error_code': None,
        'error_message': None,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""

    def _validate_api_key(self) -> bool:
        """Validate the API key from request header."""
        expected_key = os.environ.get('API_KEY')
        if not expected_key:
            # No API key configured = allow all (development mode)
            return True

        # Check X-API-Key header
        provided_key = self.headers.get('X-API-Key')
        if not provided_key:
            # Also check Authorization header as fallback
            auth_header = self.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                provided_key = auth_header[7:]

        return provided_key == expected_key

    def do_POST(self):
        """Handle POST request to send WhatsApp message."""
        # Validate API key first
        if not self._validate_api_key():
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Unauthorized - invalid or missing API key'}).encode())
            return

        # Parse request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
            return

        # Extract parameters
        phone = data.get('phone')
        message = data.get('message')
        country_code = data.get('country_code')
        template_data = data.get('template_data')  # For stock alerts or opt-in
        template_type = data.get('template_type', 'alert')  # "alert" or "optin"

        # Require phone and either message or template_data
        if not phone:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing phone'}).encode())
            return

        if not message and not template_data:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing message or template_data'}).encode())
            return

        # Format phone number
        formatted_phone = format_phone_number(phone, country_code)

        # Send message (template takes priority if both provided)
        result = send_whatsapp_message(formatted_phone, message, template_data, template_type)

        # Return response
        status_code = 200 if result['success'] else 500
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, Authorization')
        self.end_headers()
