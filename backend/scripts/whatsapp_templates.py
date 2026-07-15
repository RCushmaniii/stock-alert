"""Shared WhatsApp message template definitions for StockAlert.

These recreate the two Twilio Content Templates as Meta WhatsApp message
templates (category UTILITY). Body wording is a best-effort recreation from
the variable slots documented in the old Twilio integration — the original
Twilio template text was never readable from this repo (Twilio Content
Templates live server-side, not in code). Confirm/edit the wording below
before submitting for Meta review.

Variable mapping preserved 1:1 from the Twilio templates:
  - Stock alert: {{1}}=symbol, {{2}}=price, {{3}}=direction, {{4}}=threshold
  - Opt-in:      {{1}}=stock_count
"""

STOCK_ALERT_TEMPLATE = {
    "name": "stock_price_alert",
    "language": "en_US",
    "category": "UTILITY",
    "components": [
        {
            "type": "BODY",
            "text": "StockAlert Price Alert: {{1}} is now trading at ${{2}} per share, which is {{3}} the alert threshold of ${{4}} you set in the StockAlert app.",
            "example": {"body_text": [["AAPL", "182.50", "above", "180.00"]]},
        },
    ],
}

OPTIN_TEMPLATE = {
    "name": "whatsapp_optin",
    "language": "en_US",
    "category": "UTILITY",
    "components": [
        {
            "type": "BODY",
            "text": "You've enabled WhatsApp alerts for {{1}} stock(s) in StockAlert. Reply STOP anytime to opt out.",
            "example": {"body_text": [["3"]]},
        },
        {
            "type": "BUTTONS",
            "buttons": [
                {"type": "QUICK_REPLY", "text": "Yes, enable alerts"},
                {"type": "QUICK_REPLY", "text": "No thanks"},
            ],
        },
    ],
}

ALL_TEMPLATES = [STOCK_ALERT_TEMPLATE, OPTIN_TEMPLATE]
