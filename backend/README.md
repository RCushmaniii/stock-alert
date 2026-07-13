# StockAlert Notification Backend

Simple serverless API for sending WhatsApp notifications via Twilio.

## Deploy to Vercel (Recommended)

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Deploy

```bash
cd backend
vercel
```

### 3. Set Environment Variables

In Vercel dashboard (or via CLI):

```bash
vercel env add TWILIO_SID
vercel env add TWILIO_AUTH_TOKEN
vercel env add TWILIO_WHATSAPP_NUMBER
vercel env add API_KEY
```

### 4. Get Your API URL

After deployment, you'll get a URL like:

```
https://stockalert-backend.vercel.app/api/send_whatsapp
```

## API Usage

### Send WhatsApp Message

```bash
curl -X POST https://your-app.vercel.app/api/send_whatsapp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "phone": "5551234567",
    "message": "AAPL alert: Price $150.25 exceeded threshold!",
    "country_code": "52"
  }'
```

### Response

```json
{
  "success": true,
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

## Phone Number Formatting

The API automatically formats phone numbers for different countries:

| Country   | Input      | Formatted      |
| --------- | ---------- | -------------- |
| US/Canada | 5551234567 | +15551234567   |
| Mexico    | 3315590572 | +5213315590572 |
| Spain     | 612345678  | +34612345678   |

For Mexico, the mobile prefix "1" is automatically added.

## Rate Limiting

The send endpoint enforces per-recipient (10/min, 60/hour) and global
(100/min, 2000/hour) rate limits via Upstash Redis. Exceeding a window
returns `429` with a `Retry-After` header. If Upstash isn't configured,
rate limiting fails open (requests are allowed through) rather than
blocking legitimate alerts.

## Environment Variables

| Variable                         | Description                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| TWILIO_SID                       | Twilio Account SID                                                                          |
| TWILIO_AUTH_TOKEN                | Twilio Auth Token                                                                           |
| TWILIO_WHATSAPP_NUMBER           | Your WhatsApp Business number (+13072842785)                                                |
| API_KEY                          | Secret key for authenticating StockAlert app requests                                       |
| KV_REST_API_URL                  | Rate limiting - auto-injected by the Vercel Upstash integration (legacy "Vercel KV" naming) |
| KV_REST_API_TOKEN                | Rate limiting - auto-injected by the Vercel Upstash integration (legacy "Vercel KV" naming) |
| RATE_LIMIT_PER_NUMBER_PER_MINUTE | Optional override, default `10`                                                             |
| RATE_LIMIT_PER_NUMBER_PER_HOUR   | Optional override, default `60`                                                             |
| RATE_LIMIT_GLOBAL_PER_MINUTE     | Optional override, default `100`                                                            |
| RATE_LIMIT_GLOBAL_PER_HOUR       | Optional override, default `2000`                                                           |
