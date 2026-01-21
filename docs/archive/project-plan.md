---
trigger: manual
---

Excellent — now that your **PRD** and `config.json` are defined, you’re at the perfect point to turn this into an executable roadmap.

Here’s a **high-level project plan** written in a practical, developer-friendly way so you can manage priorities, break work into phases, and know exactly what comes next.

---

# 🧭 **StockAlert Project Plan (Python + Windows Toast)**

## 🎯 **Objective**

Develop a lightweight, background-running Windows desktop app that monitors stock prices in real time and triggers toast notifications when thresholds are reached — starting with a minimal viable product (MVP) and evolving into a configurable, polished utility.

---

## 🧩 **Phase 1 — Core MVP (1–2 days)**

Goal: Get the simplest working version running on your local machine.

### Deliverables

- ✅ Single-stock monitoring loop (`stock_alert.py`)
- ✅ Uses `yfinance` to fetch prices
- ✅ Shows Windows Toast notification using `win10toast`
- ✅ Console output for debugging
- ✅ Graceful retry on connection errors

### Tasks

1. Create `StockAlert` folder and virtual environment.
2. Install dependencies (`yfinance`, `win10toast`).
3. Implement core alert logic.
4. Test with sample ticker (e.g., AAPL).
5. Verify notification behavior at threshold.

### Success Metric

Working prototype prints price updates and shows Windows toast on threshold breach.

---

## ⚙️ **Phase 2 — Configurable Multi-Stock System (2 days)**

Goal: Allow users to track multiple tickers and thresholds via `config.json`.

### Deliverables

- ✅ `config.json` file (tickers + global settings)
- ✅ Parser integrated into script
- ✅ Handles high/low thresholds per stock
- ✅ Cooldown and check interval working correctly
- ✅ Logs visible in terminal

### Tasks

1. Implement JSON parsing logic.
2. Build loop to iterate through enabled tickers.
3. Add cooldown and logging.
4. Test multiple tickers with mixed thresholds.
5. Validate error handling (bad symbol, no internet).

### Success Metric

Multiple active stocks generate correct notifications independently.

---

## 🧱 **Phase 3 — Packaging & Deployment (1 day)**

Goal: Run as a native Windows app, optionally in background or startup.

### Deliverables

- ✅ PyInstaller build: `stock_alert.exe`
- ✅ No console version (`pythonw.exe` or PyInstaller `--noconsole`)
- ✅ Shortcut created in Startup folder for auto-launch
- ✅ README installation instructions

### Tasks

1. Add minimal logging file (optional).
2. Package app using PyInstaller.
3. Create startup shortcut.
4. Test on fresh Windows user profile.

### Success Metric

Executable runs without requiring Python; alerts function identically.

---

## 🧩 **Phase 4 — Quality & Usability Enhancements (2–3 days)**

Goal: Make it stable, friendly, and maintainable.

### Deliverables

- ✅ Improved error messages and retry logic
- ✅ Logging to file (`logs/stock_alert.log`)
- ✅ Notification suppression to prevent spam
- ✅ Clear user documentation (README.md + setup steps)

### Tasks

1. Implement `logging` module for file-based logs.
2. Refine error handling for API/network exceptions.
3. Add visual polish to notifications (icons, emojis).
4. Write detailed README with screenshots and setup guide.

### Success Metric

Stable and documented build ready for testers.

---

## 🌱 **Phase 5 — Optional Upgrades / Future Roadmap**

(These can be backlog items for v2 or an open-source release.)

| Enhancement            | Description                                          |
| ---------------------- | ---------------------------------------------------- |
| GUI Config Editor      | Simple Tkinter window to edit `config.json` visually |
| Sound Notifications    | Custom .wav sounds for high/low alerts               |
| WebSocket Streaming    | Faster real-time updates using Yahoo/Alpaca APIs     |
| Cross-Platform Support | Use `plyer` for Mac/Linux notifications              |
| Taskbar Icon & Menu    | Tray icon to toggle notifications or exit            |
| Config Reloading       | Hot reload without restart                           |
| Auto-Updater           | Script checks for new GitHub releases                |

---

## 🕒 **Estimated Timeline**

| Phase                  | Duration    | Output                            |
| ---------------------- | ----------- | --------------------------------- |
| Phase 1                | 1–2 days    | Local MVP single stock            |
| Phase 2                | 2 days      | Multi-stock with config.json      |
| Phase 3                | 1 day       | Windows executable                |
| Phase 4                | 2–3 days    | Polished stable version           |
| **Total MVP Delivery** | **~1 week** | End-to-end working StockAlert app |

---

## 🧩 **Roles / Focus Areas**

- **Robert (Lead Dev)** – architecture, Python logic, config design.
- **Tester (optional)** – verify notifications, stress test multiple tickers.
- **Designer (optional)** – icon + notification branding for v2.

---

## ✅ **Immediate Next Steps**

1. **Complete Phase 1 testing:** ensure single-ticker version runs cleanly.
2. **Create `config.json`** in your `/StockAlert` folder.
3. **Start Phase 2:** integrate config file parsing and multi-ticker support.
4. **Add logs** and error handling to prepare for packaging.

---

Would you like me to generate a **Kanban-style task breakdown** (e.g., “To-Do / In-Progress / Done”) next — something you can paste directly into GitHub Projects or Trello?
It’s a great way to visualize and assign each of these phases for the coming week.
