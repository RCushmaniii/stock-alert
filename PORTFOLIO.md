---
# === CONTROL FLAGS ===
portfolio_enabled: true
portfolio_priority: 3
portfolio_featured: true

# === CARD DISPLAY ===
title: "AI StockAlert"
tagline: "Windows desktop app for real-time stock alerts via WhatsApp and Windows notifications"
slug: "ai-stock-alert"
category: "Tools"
tech_stack:
  - "Python"
  - "PyQt6"
  - "Finnhub API"
  - "Twilio/WhatsApp"
  - "Vercel Serverless"
thumbnail: "/images/stockalert-thumb.jpg"
status: "Production"

# === DETAIL PAGE ===
problem: "Active traders need to monitor multiple stock positions simultaneously but can't watch screens all day. Existing solutions are too complex, require expensive subscriptions, or lack reliable mobile notifications that actually get seen."
solution: "A professional Windows desktop application that monitors stock prices in real-time and sends instant alerts via both Windows toast notifications and WhatsApp messages when prices cross user-defined thresholds. It runs silently in the system tray with zero subscription fees."
key_features:
  - "Real-time price monitoring for up to 15 stocks with configurable intervals and automatic market hours detection"
  - "Multi-channel alerts: Windows toast notifications with audio plus WhatsApp mobile messages via Twilio"
  - "Smart consolidated notifications — multiple alerts combined into a single notification per check cycle"
  - "Bilingual interface (EN/ES) with multi-currency display toggling between USD and MXN with live exchange rates"
  - "Background service runs silently in system tray — alerts work even when UI is closed, auto-starts with Windows"

# === MEDIA: PORTFOLIO SLIDES ===
slides:
  - src: "/images/stockalert-01.png"
    alt_en: "Moving From Market Noise to Actionable Signal — hero slide with laptop and WhatsApp phone"
    alt_es: "Del ruido del mercado a la senal accionable — diapositiva principal con laptop y WhatsApp"
  - src: "/images/stockalert-02.png"
    alt_en: "The Trap of Manual Monitoring — the gap between wanting to know and finding out in time"
    alt_es: "La trampa del monitoreo manual — la brecha entre querer saber y enterarse a tiempo"
  - src: "/images/stockalert-03.png"
    alt_en: "Why Traditional Tools Fail — email alerts buried, push notifications swiped away, terminals cost $20-$200/month"
    alt_es: "Por que fallan las herramientas tradicionales — emails enterrados, notificaciones ignoradas, terminales de $20-$200/mes"
  - src: "/images/stockalert-04.png"
    alt_en: "The Message You Actually Check — WhatsApp alert on phone, the app you check 50+ times a day"
    alt_es: "El mensaje que realmente revisas — alerta de WhatsApp en tu telefono, la app que revisas mas de 50 veces al dia"
  - src: "/images/stockalert-05.png"
    alt_en: "Intelligent Background Monitoring — auto-starts with Windows, filters for market hours, instant delivery"
    alt_es: "Monitoreo inteligente en segundo plano — inicio automatico con Windows, filtrado por horario de mercado, entrega instantanea"
  - src: "/images/stockalert-06.png"
    alt_en: "A Business Model That Respects the User — one-time purchase, bring your own key, no subscription fatigue"
    alt_es: "Un modelo de negocio que respeta al usuario — compra unica, trae tu propia clave, sin fatiga de suscripcion"
  - src: "/images/stockalert-07.png"
    alt_en: "Your Data Stays on Your Device — local first, no cloud accounts, API keys never leave your machine"
    alt_es: "Tus datos se quedan en tu dispositivo — local primero, sin cuentas en la nube, las claves API nunca salen de tu maquina"
  - src: "/images/stockalert-08.png"
    alt_en: "Beyond Code: A Case Study in Product Strategy — pain points mapped to real solutions"
    alt_es: "Mas alla del codigo: un caso de estudio en estrategia de producto — problemas reales mapeados a soluciones reales"
  - src: "/images/stockalert-09.png"
    alt_en: "Trust-Building Commerce — the anti-SaaS model with no forced retention, no account creation, no hidden fees"
    alt_es: "Comercio basado en confianza — el modelo anti-SaaS sin retencion forzada, sin creacion de cuentas, sin tarifas ocultas"
  - src: "/images/stockalert-10.png"
    alt_en: "The Bottom Line — solves a manual problem, leverages WhatsApp, respects the user's wallet and privacy"
    alt_es: "En resumen — resuelve un problema manual, aprovecha WhatsApp, respeta la billetera y la privacidad del usuario"

# === MEDIA: VIDEO ===
video_url: "/video/AI-StockAlert-brief.mp4"
video_poster: "/video/AI-StockAlert-brief-poster.jpg"

# === OPTIONAL ===
metrics:
  - "Sub-2-second alert delivery from price change detection to notification"
  - "15 stocks monitored simultaneously on free tier"
  - "60 API calls/minute rate-limited token bucket for optimal Finnhub usage"
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
