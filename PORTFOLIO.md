---
# === CONTROL FLAGS ===
portfolio_enabled: true
portfolio_priority: 3
portfolio_featured: true

# === CARD DISPLAY ===
title: "AI StockAlert"
tagline: "Professional Windows desktop application for real-time stock price monitoring with intelligent multi-channel alerting via Windows notifications and WhatsApp."
slug: "ai-stock-alert"
category: "Tools"
tech_stack:
  - "Python"
  - "PyQt6"
  - "Finnhub API"
  - "Twilio/WhatsApp Business API"
  - "cx_Freeze"
  - "Vercel Serverless"
thumbnail: "public/images/stockalert-thumb.jpg"
status: "Production"

# === DETAIL PAGE ===
problem: "Active traders and investors need to monitor multiple stock positions simultaneously but can't watch screens all day. Missing critical price movements can result in significant financial losses or missed opportunities. Existing solutions are either too complex, require expensive subscriptions, or lack reliable mobile notifications."

solution: "AI StockAlert is a professional Windows desktop application that monitors stock prices in real-time and sends instant alerts when prices cross user-defined thresholds. It combines the reliability of Windows desktop notifications with the convenience of WhatsApp mobile alerts, ensuring users never miss important price movements."

key_features:
  - "Real-time price monitoring for up to 15 stocks with configurable check intervals (free tier)"
  - "Multi-channel alerts: Windows toast notifications with audio and WhatsApp mobile messages"
  - "Smart consolidated notifications - multiple alerts combined into single notification per check cycle"
  - "Automatic market hours detection - only monitors during US market hours (9:30 AM - 4:00 PM ET)"
  - "Bilingual interface (English/Spanish) with full i18n support"
  - "Multi-currency display: Toggle between USD and Mexican Pesos (MXN) with live exchange rates"
  - "Background service runs silently in system tray - alerts work even when UI is closed"
  - "Company profile enrichment with logos, industry, and market cap data from Finnhub"
  - "Integrated news feed for monitored stocks (up to 5 tickers)"
  - "Professional installer with Windows Start Menu integration and auto-start capability"
  - "Dark/light theme support with one-click toggle"

metrics:
  - "Sub-2-second alert delivery from price change detection to notification"
  - "15 stocks monitored simultaneously on free tier"
  - "60 API calls/minute rate-limited token bucket for optimal Finnhub usage"

# === LINKS ===
demo_url: ""
live_url: "https://aistockalert.app/"

# === OPTIONAL ===
hero_images:
  - path: "public/images/stockalert-01.png"
    alt: "AI StockAlert main dashboard"
    caption: "Real-time stock monitoring dashboard with live prices and alert status."
  - path: "public/images/stockalert-02.png"
    alt: "AI StockAlert alert configuration"
    caption: "Configure price thresholds with above/below triggers for each stock."
  - path: "public/images/stockalert-03.png"
    alt: "AI StockAlert settings panel"
    caption: "Full settings panel with API key, language, theme, and notification preferences."
  - path: "public/images/stockalert-04.png"
    alt: "AI StockAlert WhatsApp integration"
    caption: "WhatsApp mobile alerts deliver price notifications anywhere."
  - path: "public/images/stockalert-05.png"
    alt: "AI StockAlert system tray"
    caption: "Runs silently in the system tray — monitoring continues even when the window is closed."
  - path: "public/images/stockalert-06.png"
    alt: "AI StockAlert Windows notification"
    caption: "Native Windows toast notifications with stock details and audio alerts."
  - path: "public/images/stockalert-07.png"
    alt: "AI StockAlert dark theme"
    caption: "Dark theme for comfortable monitoring during extended sessions."
  - path: "public/images/stockalert-08.png"
    alt: "AI StockAlert company profiles"
    caption: "Enriched company profiles with logos, industry, and market cap data."
  - path: "public/images/stockalert-09.png"
    alt: "AI StockAlert news feed"
    caption: "Integrated news feed for monitored stocks keeps you informed."
  - path: "public/images/stockalert-10.png"
    alt: "AI StockAlert multi-currency display"
    caption: "Toggle between USD and MXN with live exchange rate conversion."
video_brief:
  path: "public/video/AI_StockAlert__A_Case_Study.mp4"
  poster: "public/video/AI-StockAlert-A-Case-Study-poster.jpg"
  alt: "AI StockAlert case study — real-time stock monitoring with multi-channel alerts"
  caption: "Product case study showcasing AI StockAlert's real-time monitoring, Windows notifications, and WhatsApp alert delivery."
tags:
  - "desktop-app"
  - "fintech"
  - "python"
  - "pyqt"
  - "real-time"
  - "notifications"
  - "whatsapp"
date_completed: "2026-02"
---

## Overview

AI StockAlert is a commercial-grade Windows desktop application designed for traders and investors who need reliable, real-time stock price monitoring without being tied to their screens. The application runs quietly in the system tray, continuously monitoring configured stocks and delivering instant alerts through multiple channels when prices cross user-defined thresholds.

## Technical Architecture

The application follows a modern Python architecture with clear separation of concerns:

- **Frontend**: PyQt6-based GUI with dark/light theme support, responsive layouts, and professional CushLabs branding
- **Backend Service**: Headless monitoring service that runs independently, enabling alerts even when the GUI is closed
- **API Layer**: Finnhub integration with intelligent rate limiting (token bucket algorithm) to maximize free tier usage
- **Notification System**: Multi-channel delivery via Windows toast notifications and WhatsApp Business API through a Vercel serverless backend
- **IPC**: Named pipes for communication between GUI and background service, enabling config hot-reloading

## Key Challenges Solved

**WhatsApp Business Integration**: Implemented a secure serverless backend on Vercel to handle Twilio/WhatsApp API calls, avoiding the need to bundle sensitive credentials in the desktop executable. The system uses approved message templates that comply with Meta's quality guidelines.

**Frozen Build Complexity**: Overcame numerous challenges with cx_Freeze packaging including pywin32 DLL loading, Qt plugin bundling, and locale file path resolution in frozen executables.

**Single-Instance Architecture**: Implemented robust single-process detection using file locking and Windows mutexes, with IPC-based window activation when users launch the app while it's already running.

## Business Value

AI StockAlert enables traders to stay informed about their positions without constant screen monitoring. The combination of desktop and mobile notifications ensures critical price movements are never missed, whether the user is at their computer or away. The free tier provides genuine utility while establishing a path to premium features for power users.
