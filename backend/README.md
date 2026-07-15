# StockAlert Notification Backend

Simple serverless API for sending WhatsApp notifications via Meta's WhatsApp
Cloud API (Graph API), called directly — no BSP SDK in the send path.

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
vercel env add WHATSAPP_TOKEN
vercel env add WHATSAPP_PHONE_NUMBER_ID
vercel env add WHATSAPP_WABA_ID
vercel env add GRAPH_API_VERSION
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
  "message_sid": "wamid.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
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

| Variable                         | Description                                                                                                         |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| WHATSAPP_TOKEN                   | Meta System User access token (never-expiry, `whatsapp_business_messaging` + `whatsapp_business_management` scopes) |
| WHATSAPP_PHONE_NUMBER_ID         | Meta-issued Phone Number ID (not the raw phone number)                                                              |
| WHATSAPP_WABA_ID                 | WhatsApp Business Account ID (used for template management)                                                         |
| GRAPH_API_VERSION                | Graph API version, e.g. `v25.0`                                                                                     |
| API_KEY                          | Secret key for authenticating StockAlert app requests                                                               |
| KV_REST_API_URL                  | Rate limiting - auto-injected by the Vercel Upstash integration (legacy "Vercel KV" naming)                         |
| KV_REST_API_TOKEN                | Rate limiting - auto-injected by the Vercel Upstash integration (legacy "Vercel KV" naming)                         |
| RATE_LIMIT_PER_NUMBER_PER_MINUTE | Optional override, default `10`                                                                                     |
| RATE_LIMIT_PER_NUMBER_PER_HOUR   | Optional override, default `60`                                                                                     |
| RATE_LIMIT_GLOBAL_PER_MINUTE     | Optional override, default `100`                                                                                    |
| RATE_LIMIT_GLOBAL_PER_HOUR       | Optional override, default `2000`                                                                                   |

The underlying phone number (+13072842785) is still purchased/hosted through
Twilio, but Twilio is no longer in the WhatsApp send path — see
`operating-system/cushlabs/whatsapp-infrastructure.md` for the full picture.
