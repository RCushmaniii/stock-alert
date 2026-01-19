# StockAlert v3.0 User Guide

## Overview

StockAlert is a Windows desktop application that monitors stock prices in real-time and sends you notifications when prices cross your configured thresholds. The application runs quietly in your system tray and only actively monitors during US market hours.

## Getting Started

### Installation

1. Download the latest `StockAlert-3.0.0-win64.msi` from the releases page
2. Run the installer and follow the prompts
3. Launch StockAlert from the Start Menu

### First-Time Setup

1. **Get a Finnhub API Key** (Free)
   - Visit [finnhub.io/register](https://finnhub.io/register)
   - Create an account and copy your API key
   - The free tier allows 60 API calls per minute

2. **Configure the API Key**
   - Create a file named `.env` in the StockAlert installation folder
   - Add the line: `FINNHUB_API_KEY=your_api_key_here`
   - Or set it as a Windows environment variable

3. **Add Your First Stock**
   - Open StockAlert Configuration from the Start Menu
   - Go to the "Tickers" tab
   - Click "Add Ticker"
   - Enter a stock symbol (e.g., AAPL)
   - Set your high and low price thresholds
   - Click Save

## Main Window

### Settings Tab

| Setting | Description | Default |
|---------|-------------|---------|
| Check Interval | How often to check stock prices (seconds) | 60 |
| Cooldown Period | Time between repeated alerts for the same stock | 300 |
| Enable Notifications | Show Windows toast notifications | Yes |
| Language | Application language (English/Spanish) | English |

### Tickers Tab

The ticker table shows all your configured stocks with:
- **Symbol**: Stock ticker symbol
- **Name**: Company name
- **High Threshold**: Alert when price goes above this
- **Low Threshold**: Alert when price falls below this
- **Last Price**: Most recently fetched price
- **Enabled**: Whether monitoring is active for this stock

#### Adding a Ticker

1. Click "Add Ticker"
2. Enter the stock symbol (automatically uppercased)
3. Optionally click "Validate" to verify the symbol exists
4. Enter a display name (optional, defaults to symbol)
5. Set your high threshold (price to trigger "price too high" alert)
6. Set your low threshold (price to trigger "price too low" alert)
7. Click Save

#### Editing a Ticker

1. Select a ticker in the table
2. Click "Edit Ticker"
3. Modify the name, thresholds, or enabled status
4. Click Save

#### Deleting a Ticker

1. Select a ticker in the table
2. Click "Delete Ticker"
3. Confirm the deletion

## System Tray

StockAlert runs in your Windows system tray. Right-click the icon to access:

- **Show/Hide Window**: Toggle the main configuration window
- **Monitoring Status**: Shows how many stocks are being monitored
- **Market Status**: Current market status (open/closed/holiday)
- **Start/Stop Monitoring**: Pause or resume monitoring
- **Reload Config**: Reload configuration without restarting
- **Exit**: Completely close the application

Double-click the tray icon to show/hide the main window.

## Alerts

When a stock price crosses your threshold:

1. A Windows toast notification appears with:
   - The stock symbol and whether it's a high or low alert
   - The current price and your threshold
   - A "View Chart" button to open Yahoo Finance

2. After an alert, the stock enters a cooldown period (default 5 minutes) to prevent spam

### Alert Types

- **High Alert**: Price rose above your high threshold
- **Low Alert**: Price fell below your low threshold

## Market Hours

StockAlert is aware of US stock market hours and will:

- **Monitor actively** during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
- **Sleep automatically** when markets are closed
- **Skip holidays** (New Year's, MLK Day, Presidents' Day, Good Friday, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, Christmas)

The application uses minimal system resources when markets are closed.

## Troubleshooting

### No price data appearing

- Verify your Finnhub API key is set correctly
- Check your internet connection
- Verify the stock symbol is valid (use the Validate button)

### Not receiving notifications

- Check that notifications are enabled in Settings
- Verify Windows notifications are not in Do Not Disturb mode
- Check Windows notification settings for StockAlert

### High CPU/memory usage

- Reduce the number of monitored stocks
- Increase the check interval
- The Finnhub free tier allows 60 calls/minute, so with many stocks, checks are automatically spaced out

### Application won't start

- Check the Windows Event Viewer for errors
- Verify .NET Framework prerequisites are met
- Try running as Administrator

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save settings |
| Escape | Close current dialog |
| Delete | Delete selected ticker |

## Data & Privacy

- StockAlert only connects to Finnhub's API for stock data
- No personal data is collected or transmitted
- Your configuration is stored locally in `config.json`
- See the Privacy Policy for more details

## Support

For help or to report issues:
- GitHub Issues: [github.com/rcushman/stockalert/issues](https://github.com/rcushman/stockalert/issues)
- Email: support@rcsoftware.com
