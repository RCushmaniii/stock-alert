# Privacy Policy

**StockAlert v3.0**
**Last Updated: January 2025**

RC Software ("we", "our", or "us") respects your privacy. This Privacy Policy explains how StockAlert handles your information.

## Summary

- **We do not collect personal data**
- **We do not track your usage**
- **Your configuration stays on your computer**
- **We only connect to Finnhub for stock data**

## Information We Don't Collect

StockAlert does **NOT** collect, store, or transmit:

- Personal identification information
- Financial information or account details
- Usage statistics or analytics
- Location data
- Device identifiers
- Browsing history
- Any telemetry data

## Information Stored Locally

StockAlert stores the following information **locally on your computer only**:

### Configuration File (config.json)
- Stock symbols you choose to monitor
- Price thresholds you set
- Application preferences (check interval, language, etc.)

### Log Files (if enabled)
- Timestamps of price checks
- Alert triggers
- Error messages for troubleshooting

**This data never leaves your computer** and is not transmitted to RC Software or any third party.

## Third-Party Services

### Finnhub Stock Data API

StockAlert connects to Finnhub (finnhub.io) to retrieve stock price data. When you use StockAlert:

- Your computer sends stock symbol queries to Finnhub's servers
- Finnhub may log your IP address and API usage according to their privacy policy
- We have no control over Finnhub's data practices

Please review [Finnhub's Privacy Policy](https://finnhub.io/terms-of-service) for information about their data handling.

### What We Send to Finnhub
- Stock ticker symbols (e.g., "AAPL", "MSFT")
- Your Finnhub API key (that you provide)

### What We Don't Send
- Personal information
- Your threshold settings
- Alert history
- Any identifying information about you

## Your API Key

You are responsible for:
- Obtaining your own Finnhub API key
- Keeping your API key confidential
- Complying with Finnhub's terms of service

We recommend:
- Not sharing your API key
- Storing it securely in the `.env` file
- Not committing your `.env` file to version control

## Data Security

Since all your data is stored locally:

- **You control your data** - It's on your computer
- **You can delete it anytime** - Just delete config.json
- **No cloud storage** - Nothing synced to remote servers
- **No account required** - No registration, no login

## Children's Privacy

StockAlert is not intended for use by children under 13. We do not knowingly collect information from children.

## Changes to This Policy

We may update this Privacy Policy from time to time. Changes will be noted with a new "Last Updated" date. Continued use of StockAlert after changes constitutes acceptance of the updated policy.

## Your Rights

Since we don't collect your data:
- There's nothing to request access to
- There's nothing to delete from our servers
- There's nothing to opt out of

Your local data is entirely under your control.

## Open Source Components

StockAlert uses open source libraries. These libraries may have their own privacy implications. See THIRD_PARTY_LICENSES.md for details.

## Contact Us

If you have questions about this Privacy Policy:

RC Software
Email: privacy@rcsoftware.com
Website: https://rcsoftware.com

---

**Last Updated: January 2025**
