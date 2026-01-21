---
trigger: manual
---

Absolutely — let’s build a **realistic example `config.json`** file for your **StockAlert** project and then break it down line-by-line so your team fully understands how it works and what each key controls.

---

## 🧩 **Example: `config.json`**

```json
{
  "settings": {
    "check_interval": 60,
    "cooldown": 300,
    "currency_display": "USD",
    "notifications_enabled": true,
    "log_to_console": true
  },

  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "high_threshold": 190.0,
      "low_threshold": 180.0,
      "enabled": true
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft Corp.",
      "high_threshold": 410.0,
      "low_threshold": 375.0,
      "enabled": true
    },
    {
      "symbol": "NVDA",
      "name": "NVIDIA Corp.",
      "high_threshold": 1250.0,
      "low_threshold": 1150.0,
      "enabled": false
    }
  ]
}
```

---

## 🧠 **Section Breakdown**

### 🔹 1. `settings`

This section controls **global app behavior** — how often prices are checked, how long to wait after an alert, and whether to show logs.

| Key                     | Type    | Description                                                       | Example                          |
| ----------------------- | ------- | ----------------------------------------------------------------- | -------------------------------- |
| `check_interval`        | integer | How many seconds between each API check per ticker.               | `60` means check every 1 minute. |
| `cooldown`              | integer | How many seconds to pause _after_ an alert fires (prevents spam). | `300` means 5 minutes.           |
| `currency_display`      | string  | For cosmetic display in notifications. Doesn’t affect API logic.  | `"USD"`                          |
| `notifications_enabled` | boolean | Enables/disables Windows Toast popups.                            | `true`                           |
| `log_to_console`        | boolean | Prints ticker prices and events to terminal.                      | `true`                           |

These are ideal for early testing — you can tweak timing and verbosity without editing the code.

---

### 🔹 2. `tickers`

This is an **array of tracked stocks**, where each object defines an individual stock’s parameters.

Each entry includes:

| Key              | Type    | Description                                                                  |
| ---------------- | ------- | ---------------------------------------------------------------------------- |
| `symbol`         | string  | The official ticker symbol used by Yahoo Finance (e.g., `"AAPL"`, `"MSFT"`). |
| `name`           | string  | Optional label for display in alerts.                                        |
| `high_threshold` | float   | When price **≥** this value, trigger an upward alert.                        |
| `low_threshold`  | float   | When price **≤** this value, trigger a downward alert.                       |
| `enabled`        | boolean | Toggle individual tracking on/off without deleting the record.               |

This allows you to maintain a full list of watchlist tickers while selectively activating a few.

---

## ⚙️ **How It Would Be Used in the Python Script**

Here’s a short conceptual snippet showing how your app would consume this file:

```python
import json
import time
import yfinance as yf
from win10toast import ToastNotifier

# Load configuration
with open("config.json", "r") as f:
    config = json.load(f)

settings = config["settings"]
tickers = config["tickers"]

toaster = ToastNotifier()

def get_price(symbol):
    data = yf.Ticker(symbol)
    return data.history(period="1m")["Close"].iloc[-1]

while True:
    for item in tickers:
        if not item["enabled"]:
            continue
        price = get_price(item["symbol"])
        print(f"{item['symbol']}: ${price:.2f}")

        if price >= item["high_threshold"]:
            toaster.show_toast(
                "📈 Stock Alert",
                f"{item['name']} hit ${price:.2f} (↑ {item['high_threshold']})",
                duration=10
            )
            time.sleep(settings["cooldown"])
        elif price <= item["low_threshold"]:
            toaster.show_toast(
                "📉 Stock Alert",
                f"{item['name']} dropped to ${price:.2f} (↓ {item['low_threshold']})",
                duration=10
            )
            time.sleep(settings["cooldown"])

        time.sleep(settings["check_interval"])
```

This simple loop:

- Reads all **enabled tickers**.
- Checks price every `check_interval` seconds.
- Shows a toast notification if price breaks either threshold.
- Waits out the `cooldown` before resuming checks (to avoid repeated alerts).

---

## 🧾 **Config Summary (For Documentation)**

**File:** `/StockAlert/config.json`

**Editable Fields:**

- ✅ User can freely modify symbols, names, and thresholds.
- ⚠️ Do not remove `"settings"` or `"tickers"` keys (required by parser).
- 🔄 Changes take effect on next app start (or when config reload is implemented in future version).

---

## 🧩 **Optional Enhancements for Later Versions**

You could expand this config in future versions with:

- `sound_file`: path to a custom `.wav` for each stock alert.
- `notify_once`: boolean to stop further alerts once threshold is hit.
- `check_source`: choose between Yahoo Finance or another API.
- `color_theme`: if you later add a small GUI.

---

Would you like me to generate the **improved Python version** that dynamically reads this JSON config (multi-ticker loop, thresholds, and cooldowns all implemented cleanly with logging)?
That would make your MVP fully functional and aligned with the PRD.
