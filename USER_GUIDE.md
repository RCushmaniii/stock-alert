# 📈 StockAlert - User Guide

Welcome to **StockAlert**! This application monitors stock prices in real-time and sends you Windows notifications when prices cross your custom thresholds.

---

## 🚀 Quick Start

### ⚠️ Windows Defender / SmartScreen Warning

When installing, you may see a Windows Defender or SmartScreen warning. **This is normal for new applications** that don't have a code signing certificate yet.

**Why this happens:**
- StockAlert is a new application without widespread distribution
- It's not digitally signed with an expensive code signing certificate
- Windows is being cautious with unfamiliar software

**StockAlert is safe:**
- ✅ Open source - you can review all code
- ✅ No network activity except Yahoo Finance API
- ✅ No data collection or telemetry
- ✅ No admin privileges required
- ✅ Scanned by VirusTotal (0 detections)

**To install anyway:**

1. **If you see "Windows protected your PC":**
   - Click **"More info"**
   - Click **"Run anyway"**

2. **If Windows Defender blocks it:**
   - Click **"Show more"** or **"Actions"**
   - Select **"Allow on device"**

3. **If still blocked:**
   - Open **Windows Security**
   - Go to **Virus & threat protection** → **Protection history**
   - Find StockAlert and select **"Allow"**

**Future versions will be code-signed to eliminate these warnings.**

### First Time Setup

1. **Open StockAlert Configuration**
   - Click **Start Menu** → **StockAlert Configuration**
   - This opens the configuration tool where you can manage your stocks

2. **Configure Your Stocks**
   - The app comes with example stocks (AAPL, MSFT) already configured
   - You can modify these or add your own stocks

3. **Start Monitoring**
   - Click **Start Menu** → **StockAlert**
   - The app runs invisibly in the background (system tray)
   - Look for the StockAlert icon in your system tray (bottom-right)
   - You'll receive Windows notifications when prices cross your thresholds
   - **Automatically monitors only during market hours** (9:30 AM - 4:00 PM ET, Mon-Fri)
   - Right-click the tray icon for options

---

## 📱 What's Included

### StockAlert.exe
**The main monitoring application (Background Tray)**

- Runs invisibly in the Windows system tray
- Monitors stock prices in real-time during market hours only
- Sends Windows Toast notifications when thresholds are crossed
- Automatically sleeps when market is closed (nights, weekends, holidays)
- Wakes up when market opens
- Right-click tray icon for menu options

**When to use:** Add to Windows Startup to run automatically

**Tray Icon Menu:**
- View market status
- See number of stocks being monitored
- Open Configuration tool
- Reload configuration
- Exit application

### StockAlertConfig.exe
**The configuration tool**

- Add, edit, or remove stocks from your watchlist
- Set high and low price thresholds for each stock
- Adjust check interval (how often to check prices)
- Configure cooldown period (prevents notification spam)
- Enable/disable individual stocks without deleting them

**When to use:** Run this whenever you want to change your stock settings

---

## ⚙️ Configuration Guide

### Settings Tab

**Check Interval (seconds)**
- How often to check stock prices
- Default: 60 seconds
- Range: 10-3600 seconds
- *Lower values = more frequent checks but more API calls*

**Cooldown Period (seconds)**
- Time between alerts for the same stock
- Default: 300 seconds (5 minutes)
- Range: 60-86400 seconds
- *Prevents getting spammed with notifications*

**Notifications Enabled**
- Turn all notifications on/off
- Useful if you want to monitor without alerts

### Tickers Tab

**Adding a Stock:**
1. Click **Add Ticker**
2. Enter stock symbol (e.g., AAPL, MSFT, TSLA)
3. Click **Validate** to verify the symbol exists
4. Set **High Threshold** - Alert when price goes above this
5. Set **Low Threshold** - Alert when price goes below this
6. Click **Save**

**Editing a Stock:**
1. Select the stock from the list
2. Modify thresholds or settings
3. Click **Save**

**Removing a Stock:**
1. Select the stock from the list
2. Click **Delete**

**Disabling a Stock (without deleting):**
1. Select the stock
2. Uncheck **Enabled**
3. Click **Save**

---

## 🔔 Understanding Notifications

### When You'll Get Alerts

You'll receive a Windows Toast notification when:
- Stock price crosses **above** your high threshold
- Stock price crosses **below** your low threshold

### Cooldown Period

After an alert is sent, the same stock won't alert again until the cooldown period expires. This prevents notification spam if a stock price hovers around your threshold.

**Example:**
- AAPL high threshold: $190
- Cooldown: 300 seconds (5 minutes)
- If AAPL hits $191, you get an alert
- Even if AAPL stays at $191, you won't get another alert for 5 minutes

### Clicking Notifications

Click on a notification to open the stock's chart on Yahoo Finance in your web browser.

---

## 💡 Tips & Best Practices

### Setting Good Thresholds

1. **Check current price first** on [Yahoo Finance](https://finance.yahoo.com)
2. **Set realistic thresholds** based on typical price movements
3. **Update regularly** as stock prices change over time

**Example:**
- Current AAPL price: $185
- Set high threshold: $190 (alert if it goes up $5)
- Set low threshold: $180 (alert if it drops $5)

### Managing Multiple Stocks

- Start with 2-3 stocks to test
- Add more once you're comfortable
- Use the **Enabled** checkbox to temporarily disable stocks

### Check Interval Recommendations

- **Day trading:** 10-30 seconds (very frequent)
- **Active monitoring:** 60 seconds (default)
- **Casual watching:** 300-600 seconds (5-10 minutes)

### Cooldown Recommendations

- **Frequent updates:** 60-180 seconds
- **Balanced (default):** 300 seconds (5 minutes)
- **Minimal alerts:** 600-1800 seconds (10-30 minutes)

---

## 🐛 Troubleshooting

### No Notifications Appearing?

**Check Windows Settings:**
1. Open **Settings** → **System** → **Notifications**
2. Ensure notifications are enabled
3. Find **StockAlert** in the app list
4. Make sure it has notification permission

**Check App Settings:**
1. Open **StockAlert Configuration**
2. Go to **Settings** tab
3. Ensure **Notifications Enabled** is checked

**Verify Thresholds:**
- Make sure your thresholds make sense for current prices
- Check if cooldown period is blocking alerts (see console output)

### "No data available" Error?

- ✅ Check your internet connection
- ✅ Verify the stock symbol on [Yahoo Finance](https://finance.yahoo.com)
- ✅ Try again (API can be slow sometimes)
- ✅ Note: Some international stocks may not be available

### Symbol Validation Fails?

- Use official ticker symbols (e.g., `AAPL` not `Apple`)
- Search on Yahoo Finance first to find the correct symbol
- Some stocks may not be available through the API

### App Crashes on Startup?

**Check config.json:**
1. Navigate to `C:\Program Files\StockAlert`
2. Delete `config.json`
3. Restart the app (it will recreate from example)

**Or use the config editor:**
1. Open **StockAlert Configuration**
2. Fix any invalid settings
3. Save and try again

### Console Window Closes Immediately?

This usually means there's a configuration error. To see the error:
1. Open PowerShell or Command Prompt
2. Navigate to: `cd "C:\Program Files\StockAlert"`
3. Run: `.\StockAlert.exe`
4. Read the error message

---

## 📂 File Locations

### Installation Directory
```
C:\Program Files\StockAlert\
```

### Configuration File
```
C:\Program Files\StockAlert\config.json
```

This file stores all your settings and stocks. You can:
- ✅ Edit it manually (if you know JSON)
- ✅ Back it up to save your configuration
- ✅ Share it with others

### Start Menu Shortcuts
```
Start Menu → StockAlert
Start Menu → StockAlert Configuration
```

---

## 🔧 Advanced Usage

### Editing config.json Manually

The configuration file is in JSON format. You can edit it with Notepad:

```json
{
  "settings": {
    "check_interval": 60,
    "cooldown": 300,
    "notifications_enabled": true
  },
  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "high_threshold": 190.0,
      "low_threshold": 180.0,
      "enabled": true
    }
  ]
}
```

**After editing manually:**
- Save the file
- Restart StockAlert for changes to take effect

### Backing Up Your Configuration

1. Navigate to `C:\Program Files\StockAlert`
2. Copy `config.json` to a safe location
3. To restore: Copy it back and restart the app

### Market Hours Detection (Automatic!)

**Good news:** StockAlert automatically knows when the market is open!

**US Market Hours (Eastern Time):**
- Regular hours: 9:30 AM - 4:00 PM (Mon-Fri)
- Pre-market: 4:00 AM - 9:30 AM
- After-hours: 4:00 PM - 8:00 PM
- Closed: Nights, weekends, holidays

**How it works:**
- When market is **open**: Monitors stocks every 60 seconds (or your configured interval)
- When market is **closed**: Sleeps and uses almost no resources
- Automatically wakes up when market opens
- Includes US market holiday calendar (Thanksgiving, Christmas, etc.)

### Running at Startup (Recommended!)

✅ **Recommended** - Let StockAlert run 24/7 in the background!

**Automatic Installation Script:**

1. Navigate to `C:\Program Files\StockAlert`
2. Right-click `install_startup.ps1`
3. Select **Run with PowerShell**
4. Approve the prompt

**Manual Installation:**

1. Press `Win + R`
2. Type: `shell:startup` and press Enter
3. Create a shortcut to `C:\Program Files\StockAlert\StockAlert.exe`
4. Place the shortcut in the Startup folder

**Result:** StockAlert starts automatically when you log in, runs in the system tray, and only monitors during market hours!

---

## 📊 Example Configurations

### Day Trader Setup
```
Check Interval: 10 seconds
Cooldown: 60 seconds
Stocks: 5-10 active stocks
Thresholds: Tight (±1-2% from current price)
```

### Long-Term Investor
```
Check Interval: 300 seconds (5 minutes)
Cooldown: 1800 seconds (30 minutes)
Stocks: 10-20 portfolio stocks
Thresholds: Wide (±5-10% from current price)
```

### Swing Trader
```
Check Interval: 60 seconds
Cooldown: 300 seconds (5 minutes)
Stocks: 3-5 focus stocks
Thresholds: Medium (±2-5% from current price)
```

---

## ❓ Frequently Asked Questions

**Q: Do I need Python installed?**  
A: No! Everything is included in the installer.

**Q: Does this work with international stocks?**  
A: Most stocks available on Yahoo Finance work. Try validating the symbol first.

**Q: Can I monitor cryptocurrencies?**  
A: Some crypto symbols work (e.g., BTC-USD, ETH-USD). Validate first.

**Q: Is my data private?**  
A: Yes! All data stays on your computer. The app only connects to Yahoo Finance API for prices.

**Q: Can I run this on multiple computers?**  
A: Yes! Just install the MSI on each computer. You can copy your config.json to keep the same settings.

**Q: Does this cost money?**  
A: No, it's completely free. The Yahoo Finance API is free to use.

**Q: What happens if my internet goes down?**  
A: The app will show errors in the console but will keep trying. It will resume when internet is restored.

**Q: Can I hide the console window?**  
A: Currently, the console shows important information. A future version may add a "silent mode."

**Q: Does StockAlert run automatically when I start Windows?**  
A: Not by default, but you can easily add it to Startup. Run the included `install_startup.ps1` script or manually add a shortcut to your Startup folder.

**Q: Should I run it 24/7?**  
A: Yes! The app is designed to run 24/7. It automatically detects market hours and only monitors when the market is open (9:30 AM - 4:00 PM ET, Mon-Fri). When the market is closed, it sleeps and uses almost no resources.

**Q: How much CPU and memory does it use?**  
A: Very little! About 50-100 MB of memory. During market hours, minimal CPU (only active during price checks every 60 seconds). When market is closed, it sleeps and uses almost no CPU.

**Q: Can I minimize it to the system tray?**  
A: It runs in the system tray by default! Look for the StockAlert icon in your system tray (bottom-right corner). Right-click for options.

**Q: What happens if I close it from the tray?**  
A: Right-click the tray icon and select "Exit" to stop monitoring. You'll need to restart StockAlert.exe to resume.

**Q: Does it know about market holidays?**  
A: Yes! The app includes a US market holiday calendar and automatically skips monitoring on holidays like Thanksgiving, Christmas, etc.

---

## 🆘 Getting Help

### Error Messages

The console window shows helpful error messages. Common ones:

- **"No data available"** → Internet issue or invalid symbol
- **"Config missing"** → Run StockAlertConfig.exe to create settings
- **"Failed to fetch price"** → Temporary API issue, will retry automatically

### Still Need Help?

1. Check this guide's Troubleshooting section
2. Review the error message in the console window
3. Try deleting config.json and starting fresh
4. Contact support with the error message details

---

## 📝 Version Information

**Version:** 2.0.0  
**Platform:** Windows 10/11  
**Data Source:** Yahoo Finance API  

---

## 🙏 Thank You!

Thank you for using StockAlert! We hope it helps you stay on top of your investments.

**Happy Trading! 📈**
