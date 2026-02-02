"""
StockAlert WhatsApp Notification API

Simple serverless function to send WhatsApp messages via Twilio.
Deploy to Vercel, Cloudflare Workers, or AWS Lambda.

Supports both:
- Template messages (for business-initiated alerts)
- Free-form messages (for user-initiated session replies)
"""

import json
import os
import re
from http.server import BaseHTTPRequestHandler

from twilio.rest import Client


# Content Template SID for stock price alerts (ai_stock_price_alert_02)
STOCK_ALERT_TEMPLATE_SID = "HX138b713346901520a4a6d48e21ec3e68"

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


def send_whatsapp_message(to_number: str, message: str = None, template_data: dict = None) -> dict:
    """
    Send a WhatsApp message via Twilio.

    Args:
        to_number: Recipient phone number (E.164 format)
        message: Message text (for free-form/session messages)
        template_data: Dict with symbol, price, threshold, direction (for template messages)

    Returns:
        dict with success status and message SID or error
    """
    account_sid = os.environ.get('TWILIO_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    whatsapp_number = os.environ.get('TWILIO_WHATSAPP_NUMBER')

    if not all([account_sid, auth_token, whatsapp_number]):
        return {
            'success': False,
            'error': 'Twilio credentials not configured'
        }

    try:
        client = Client(account_sid, auth_token)

        # Format numbers for WhatsApp
        from_whatsapp = f'whatsapp:{whatsapp_number}'
        to_whatsapp = f'whatsapp:{to_number}'

        # Use template for stock alerts, free-form for test messages
        if template_data:
            # Template variables: {{1}}=symbol, {{2}}=price, {{3}}=direction, {{4}}=threshold
            # Accept both formats: {"1": "AAPL"} or {"symbol": "AAPL"}
            content_variables = json.dumps({
                "1": template_data.get("1") or template_data.get("symbol", "STOCK"),
                "2": str(template_data.get("2") or template_data.get("price", "0.00")),
                "3": template_data.get("3") or template_data.get("direction", "crossed"),
                "4": str(template_data.get("4") or template_data.get("threshold", "0.00")),
            })

            message_obj = client.messages.create(
                content_sid=STOCK_ALERT_TEMPLATE_SID,
                content_variables=content_variables,
                from_=from_whatsapp,
                to=to_whatsapp
            )
        else:
            # Free-form message (only works within 24hr session window)
            message_obj = client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=to_whatsapp
            )

        return {
            'success': True,
            'message_sid': message_obj.sid
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
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
        template_data = data.get('template_data')  # For stock alerts

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
        result = send_whatsapp_message(formatted_phone, message, template_data)

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
