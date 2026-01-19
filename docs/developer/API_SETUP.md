# API Setup Guide

This guide explains how to set up and configure the Finnhub API for StockAlert.

## Finnhub API

StockAlert uses [Finnhub](https://finnhub.io) as its stock data provider. Finnhub offers:
- Real-time stock quotes
- Symbol lookup and validation
- 60 API calls per minute on the free tier

### Getting an API Key

1. **Create a Finnhub Account**
   - Visit [finnhub.io/register](https://finnhub.io/register)
   - Sign up with your email
   - Verify your email address

2. **Get Your API Key**
   - Log in to your Finnhub dashboard
   - Your API key is displayed on the dashboard
   - Copy the key (it looks like: `c1234567890abcdef`)

3. **Keep Your Key Secure**
   - Never share your API key publicly
   - Don't commit it to version control
   - Rotate your key if it's exposed

### Configuring StockAlert

#### Method 1: Environment File (Recommended)

1. Create a `.env` file in the StockAlert directory:
   ```
   FINNHUB_API_KEY=your_api_key_here
   ```

2. StockAlert automatically loads this on startup

#### Method 2: Windows Environment Variable

1. Open System Properties > Environment Variables
2. Add a new User Variable:
   - Name: `FINNHUB_API_KEY`
   - Value: Your API key
3. Restart StockAlert

#### Method 3: Command Line (Temporary)

```powershell
$env:FINNHUB_API_KEY = "your_api_key"
python -m stockalert
```

## API Rate Limits

### Free Tier Limits

| Limit | Value |
|-------|-------|
| Calls per minute | 60 |
| Calls per day | Unlimited |
| Historical data | Limited |

### How StockAlert Handles Rate Limits

StockAlert uses a **token bucket** algorithm:

1. **Burst Capacity**: Up to 10 rapid calls allowed
2. **Refill Rate**: 1 token per second
3. **Blocking**: Requests wait when tokens are exhausted
4. **Automatic Spacing**: With many stocks, checks are spread out

#### Example Rate Calculations

| # of Stocks | Time to Check All | Effective Interval |
|-------------|-------------------|-------------------|
| 10 | 10 seconds | 60s check + 10s API = 70s cycle |
| 30 | 30 seconds | 60s check + 30s API = 90s cycle |
| 60 | 60 seconds | 60s check + 60s API = 120s cycle |

### Optimizing API Usage

1. **Reduce Stock Count**: Only monitor stocks you actively trade
2. **Increase Check Interval**: 120 seconds instead of 60
3. **Disable Unused Tickers**: Toggle off stocks you're not watching

## API Response Format

### Quote Endpoint

StockAlert calls `quote` for each monitored symbol:

```python
# Request
client.quote("AAPL")

# Response
{
    "c": 175.50,    # Current price
    "d": 2.25,      # Change
    "dp": 1.30,     # Percent change
    "h": 176.00,    # High of day
    "l": 173.00,    # Low of day
    "o": 174.00,    # Open price
    "pc": 173.25,   # Previous close
    "t": 1704067200 # Timestamp
}
```

### Symbol Lookup

Used for validating new tickers:

```python
# Request
client.symbol_lookup("Apple")

# Response
{
    "count": 4,
    "result": [
        {
            "description": "Apple Inc.",
            "displaySymbol": "AAPL",
            "symbol": "AAPL",
            "type": "Common Stock"
        },
        ...
    ]
}
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check your key is correct |
| 429 Too Many Requests | Rate limit exceeded | Wait and try again |
| Symbol returns 0 | Invalid symbol | Verify symbol exists |

### Error Codes in Logs

```
[ERROR] Finnhub API error: 401 Client Error: Unauthorized
[WARNING] Rate limit exceeded. Waiting 1.5s for token
[INFO] Symbol INVALID123 not found
```

## Alternative Providers

StockAlert's architecture supports adding new providers. To add a provider:

1. Create a new provider class implementing `BaseProvider`
2. Implement required methods:
   - `get_price(symbol)`
   - `validate_symbol(symbol)`
   - `get_quote(symbol)`
3. Add to provider factory

### Provider Interface

```python
from stockalert.api.base import BaseProvider

class NewProvider(BaseProvider):
    def get_price(self, symbol: str) -> float | None:
        """Get current price for symbol."""
        ...

    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol exists."""
        ...

    def get_quote(self, symbol: str) -> dict | None:
        """Get full quote data."""
        ...

    @property
    def name(self) -> str:
        return "NewProvider"

    @property
    def rate_limit(self) -> int:
        return 60  # calls per minute
```

## Testing Without API Key

For development without an API key:

1. **Use Mock Provider**
   ```python
   provider = MagicMock()
   provider.get_price.return_value = 175.50
   ```

2. **Run in Debug Mode**
   ```bash
   DEBUG_MODE=1 python -m stockalert
   ```

3. **Use Test Fixtures**
   ```python
   @pytest.fixture
   def mock_finnhub():
       # See conftest.py for full implementation
       ...
   ```

## API Dashboard

Monitor your API usage at [finnhub.io/dashboard](https://finnhub.io/dashboard):

- View call history
- Check remaining quota
- Regenerate API key
- Upgrade plan if needed

## Support

- Finnhub Documentation: [finnhub.io/docs](https://finnhub.io/docs)
- Finnhub Support: support@finnhub.io
- StockAlert Issues: [github.com/rcushman/stockalert/issues](https://github.com/rcushman/stockalert/issues)
