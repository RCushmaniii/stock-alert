================================================================================
                            STOCKALERT v2.1.0
          Background Stock Monitoring with Market Hours Detection
================================================================================

QUICK START
-----------

1. CONFIGURE YOUR STOCKS
   - Click Start Menu > "StockAlert Configuration"
   - Add your stocks and set price thresholds
   - Click Save

2. START MONITORING
   - Click Start Menu > "StockAlert"
   - Look for the icon in your system tray (bottom-right)
   - Right-click the icon for options

3. ENABLE AUTO-START (Optional but Recommended)
   - Navigate to this folder
   - Right-click "install_startup.ps1"
   - Select "Run with PowerShell"
   - StockAlert will now start automatically with Windows


WHAT IT DOES
------------

StockAlert monitors your stocks and sends Windows notifications when prices
cross your thresholds. It runs invisibly in the background and automatically:

  - Only monitors during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
  - Skips weekends and US market holidays
  - Sleeps when market is closed (uses almost no resources)
  - Wakes up when market opens


SYSTEM TRAY ICON
-----------------

Right-click the tray icon for:
  - View market status
  - See number of stocks being monitored
  - Open configuration tool
  - Reload configuration
  - Exit application


FILES INCLUDED
--------------

  StockAlert.exe           - Main monitoring app (runs in system tray)
  StockAlertConfig.exe     - Configuration GUI
  StockAlertConsole.exe    - Console version (for debugging)
  config.example.json      - Example configuration
  config.json              - Your settings (created on first run)
  USER_GUIDE.md            - Comprehensive user guide (open with any text editor)
  README.md                - Developer documentation
  install_startup.ps1      - Auto-start installation script


TROUBLESHOOTING
---------------

No notifications?
  - Check Windows Settings > System > Notifications
  - Ensure "StockAlert" has notification permission
  - Verify thresholds are set correctly

Can't find the tray icon?
  - Click the up arrow (^) in the system tray
  - Look for StockAlert icon
  - Right-click to access menu

App won't start?
  - Check that config.json exists in this folder
  - Run StockAlertConfig.exe to create/fix configuration
  - Try running StockAlertConsole.exe to see error messages


MARKET HOURS
------------

US Stock Market Hours (Eastern Time):
  Regular:     9:30 AM - 4:00 PM (Mon-Fri)
  Pre-market:  4:00 AM - 9:30 AM
  After-hours: 4:00 PM - 8:00 PM
  Closed:      Nights, weekends, holidays

StockAlert automatically detects market hours and only monitors when
the market is open. When closed, it sleeps and uses minimal resources.


RESOURCE USAGE
--------------

  During market hours:  50-100 MB RAM, <1% CPU
  When market closed:   1-2 MB RAM, 0% CPU

Safe to run 24/7 - it's designed for it!


NEED HELP?
----------

See USER_GUIDE.md for detailed instructions, FAQs, and troubleshooting.


VERSION
-------

Version: 2.1.0
Platform: Windows 10/11
Data Source: Yahoo Finance API (free, no API key needed)


================================================================================
                    Built with ❤️ for stock monitoring
================================================================================
