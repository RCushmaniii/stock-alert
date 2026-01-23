# StockAlert Marketing Website Specification

> Instructions for AI Developer to build the StockAlert marketing website

## Project Overview

Build a bilingual (English/Spanish) marketing website for **StockAlert**, a Windows desktop application for real-time stock price monitoring with multi-channel alerts. The website should drive downloads and conversions to premium plans.

**Live App Repository:** https://github.com/RCushmaniii/stock-alert
**Marketing Website:** https://ai-stock-alert-website.netlify.app/

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | **Next.js 14+** (App Router) |
| Styling | **Tailwind CSS** |
| i18n | **next-intl** or **next-i18next** |
| Animations | **Framer Motion** |
| Icons | **Lucide React** or **Heroicons** |
| Forms | **React Hook Form** + **Zod** |
| Hosting | **Netlify** |
| Analytics | **Google Analytics 4** or **Plausible** |

---

## Brand Guidelines

### Company
- **Company Name:** CushLabs.ai
- **Product Name:** StockAlert
- **Tagline:** "Never miss a market move"
- **Secondary Tagline:** "Real-time stock alerts. Your way."

### Color Palette

```css
/* Primary Colors */
--brand-orange: #FF6A3D;        /* Primary CTA, buttons, accents */
--brand-orange-hover: #FF8560;  /* Hover state */
--brand-orange-dark: #E55A2D;   /* Pressed state */

/* Dark Theme (Primary) */
--dark-bg: #0D0D0D;             /* Page background */
--dark-surface: #1A1A1A;        /* Cards, sections */
--dark-surface-2: #2A2A2A;      /* Elevated elements */
--dark-border: #333333;         /* Borders */
--dark-text: #FFFFFF;           /* Primary text */
--dark-text-muted: #AAAAAA;     /* Secondary text */
--dark-text-dim: #666666;       /* Tertiary text */

/* Light Theme (Secondary) */
--light-bg: #FAFAFA;
--light-surface: #FFFFFF;
--light-border: #E5E5E5;
--light-text: #000000;
--light-text-muted: #666666;

/* Semantic Colors */
--success: #00AA00;             /* Positive alerts, confirmations */
--warning: #FFAA00;             /* Warnings */
--error: #FF4444;               /* Errors */
--info: #3B82F6;                /* Information */
```

### Typography

```css
/* Font Family */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;

/* Font Sizes */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
--text-5xl: 3rem;      /* 48px */
--text-6xl: 3.75rem;   /* 60px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Design Principles

1. **Dark-first design** - Primary theme is dark, light theme available
2. **Orange accents** - Use brand orange sparingly for CTAs and highlights
3. **Clean & Professional** - Minimal clutter, generous whitespace
4. **Trust signals** - Security badges, testimonials, social proof
5. **Mobile-first** - Responsive design, touch-friendly

### Button Styles

```css
/* Primary Button (CTA) */
.btn-primary {
  background: var(--brand-orange);
  color: #000000;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.2s;
}
.btn-primary:hover {
  background: var(--brand-orange-hover);
  transform: translateY(-1px);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--dark-text);
  border: 1px solid var(--dark-border);
  padding: 12px 24px;
  border-radius: 8px;
}
.btn-secondary:hover {
  border-color: var(--brand-orange);
  color: var(--brand-orange);
}
```

---

## Internationalization (i18n)

### Language Detection Flow

```
1. Check URL path prefix (/en, /es)
2. If no prefix → Check browser Accept-Language header
3. If Spanish (es, es-*) → Redirect to /es/
4. Otherwise → Default to /en/
5. Store preference in cookie for return visits
```

### URL Structure

```
/en/                    # English home
/en/features            # English features
/en/download            # English download
/en/pricing             # English pricing
/en/contact             # English contact

/es/                    # Spanish home
/es/caracteristicas     # Spanish features (translated slug)
/es/descargar           # Spanish download
/es/precios             # Spanish pricing
/es/contacto            # Spanish contact
```

### Language Switcher

- Position: Top-right header
- Style: "EN | ES" toggle (matches app design)
- Behavior: Switch language, preserve current page

### Translation Files

Create JSON translation files for all UI text:
- `/locales/en/common.json`
- `/locales/en/home.json`
- `/locales/en/features.json`
- `/locales/es/common.json`
- `/locales/es/home.json`
- `/locales/es/features.json`

---

## Page Specifications

### Global Components

#### Header
```
[Logo: StockAlert]                    [Features] [Pricing] [Download] [EN|ES] [Get Started - CTA]
```
- Sticky on scroll with blur background
- Mobile: Hamburger menu
- CTA button always visible

#### Footer
```
[Logo]                    [Product]           [Company]           [Legal]
StockAlert                Features            About               Privacy Policy
by CushLabs.ai            Pricing             Contact             Terms of Service
                          Download            Support             EULA
© 2026 CushLabs.ai
All Rights Reserved       [Twitter] [GitHub] [LinkedIn]
```

---

### Page 1: Home (/)

**Purpose:** Hook visitors, explain value prop, drive downloads

**Sections:**

1. **Hero Section**
   ```
   [Background: Subtle stock chart animation or gradient]

   "Never Miss a Market Move"

   Real-time stock price alerts delivered to your desktop,
   WhatsApp, or email. Monitor unlimited stocks 24/7.

   [Download Free]  [See Pricing]

   [Hero Image: App screenshot showing alert notification]

   "Trusted by 1,000+ traders" (or remove if no data yet)
   ```

2. **Feature Highlights** (3-4 cards)
   ```
   [Icon] Multi-Channel Alerts
   Windows notifications, WhatsApp, email - get alerts your way.

   [Icon] Background Monitoring
   Runs silently 24/7, even when you close the app.

   [Icon] Smart Thresholds
   Set custom high/low price triggers for each stock.

   [Icon] Market Hours Aware
   Only alerts during trading hours. No weekend spam.
   ```

3. **How It Works** (3 steps)
   ```
   1. Add Your Stocks → Enter symbols, set price thresholds
   2. Choose Alerts → Windows, WhatsApp, or email
   3. Get Notified → Instant alerts when prices cross your triggers
   ```

4. **App Screenshot Gallery**
   - Show main window (Tickers tab)
   - Show notification example
   - Show settings/profile

5. **Pricing Preview**
   ```
   [Free]              [Premium]           [Pro]
   3 stocks            Unlimited           Everything
   Windows alerts      + WhatsApp/Email    + API Access
   $0                  $9.99/mo            $19.99/mo

   [Compare Plans →]
   ```

6. **Testimonials** (if available, or skip)

7. **Final CTA**
   ```
   Ready to Never Miss a Move?
   [Download StockAlert Free]
   Windows 10/11 • No credit card required
   ```

---

### Page 2: Features (/features)

**Purpose:** Deep dive into capabilities

**Sections:**

1. **Hero**
   ```
   "Powerful Features for Serious Traders"
   Everything you need to stay ahead of the market.
   ```

2. **Feature Grid** (detailed cards with screenshots)

   **Multi-Channel Alerts**
   - Windows toast notifications with sound
   - WhatsApp messages via Twilio
   - Email alerts (coming soon)
   - Click notification to view chart

   **Background Service**
   - Runs independently of GUI
   - Auto-starts with Windows (optional)
   - Minimal resource usage
   - Config hot-reload

   **Smart Monitoring**
   - Custom high/low thresholds per stock
   - Configurable check intervals (1-60 min)
   - Cooldown periods prevent alert spam
   - Market hours detection (NYSE)

   **Professional Interface**
   - Modern PyQt6 GUI
   - Dark and light themes
   - Bilingual (English/Spanish)
   - System tray integration

   **Security & Privacy**
   - API keys stored locally
   - No data sent to our servers
   - Open architecture
   - Your data stays yours

3. **Feature Comparison Table** (Free vs Premium vs Pro)

4. **CTA**
   ```
   [Download Free] or [View Pricing]
   ```

---

### Page 3: Download (/download)

**Purpose:** Convert visitors to downloads

**Sections:**

1. **Hero**
   ```
   "Download StockAlert"
   Free for Windows 10 and Windows 11
   ```

2. **Download Options**
   ```
   [RECOMMENDED]
   StockAlert Installer (MSI)
   Version 3.0.0 • 45 MB • Windows 10/11
   [Download .msi]

   [PORTABLE]
   StockAlert Portable (ZIP)
   No installation required
   [Download .zip]
   ```

3. **System Requirements**
   ```
   • Windows 10 or Windows 11
   • 100 MB free disk space
   • Internet connection
   • Finnhub API key (free)
   ```

4. **Installation Steps**
   ```
   1. Download the installer
   2. Run StockAlert-Setup.msi
   3. Get free API key from finnhub.io
   4. Enter API key on first launch
   5. Add stocks and set alerts!
   ```

5. **Quick Start Video** (optional - placeholder)

6. **FAQ Accordion**
   - Is it really free?
   - How do I get a Finnhub API key?
   - Does it work on Mac/Linux?
   - Is my data secure?

---

### Page 4: Pricing (/pricing)

**Purpose:** Convert free users to premium

**Sections:**

1. **Hero**
   ```
   "Simple, Transparent Pricing"
   Start free, upgrade when you need more.
   ```

2. **Pricing Cards**
   ```
   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
   │      FREE       │  │    PREMIUM      │  │       PRO       │
   │                 │  │   MOST POPULAR  │  │                 │
   │      $0         │  │  $9.99/month    │  │  $19.99/month   │
   │    forever      │  │  $99/year save  │  │  $199/year save │
   │                 │  │     17%         │  │      17%        │
   ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
   │ ✓ 3 stocks      │  │ ✓ Unlimited     │  │ ✓ Everything in │
   │ ✓ Windows       │  │   stocks        │  │   Premium       │
   │   alerts        │  │ ✓ WhatsApp      │  │ ✓ API access    │
   │ ✓ Basic         │  │   alerts        │  │ ✓ Priority      │
   │   monitoring    │  │ ✓ Email alerts  │  │   support       │
   │                 │  │ ✓ 1-min check   │  │ ✓ Early access  │
   │                 │  │   intervals     │  │   to features   │
   │                 │  │ ✓ Email support │  │                 │
   ├─────────────────┤  ├─────────────────┤  ├─────────────────┤
   │  [Download]     │  │  [Get Premium]  │  │   [Get Pro]     │
   └─────────────────┘  └─────────────────┘  └─────────────────┘
   ```

3. **Feature Comparison Table** (detailed)

4. **FAQ**
   - Can I upgrade later?
   - How do I cancel?
   - Is there a refund policy?
   - Do you offer team pricing?

5. **Money-back Guarantee Badge**
   ```
   30-Day Money-Back Guarantee
   Not satisfied? Full refund, no questions asked.
   ```

---

### Page 5: Contact (/contact)

**Purpose:** Support and sales inquiries

**Sections:**

1. **Hero**
   ```
   "Get in Touch"
   We'd love to hear from you.
   ```

2. **Contact Options** (cards)
   ```
   [Support]                    [Sales]
   help@cushlabs.ai            sales@cushlabs.ai
   For technical questions      For pricing and enterprise

   [GitHub]
   github.com/RCushmaniii/stock-alert
   Report bugs, request features
   ```

3. **Contact Form**
   ```
   Name: [____________]
   Email: [____________]
   Subject: [Dropdown: Support / Sales / Feedback / Other]
   Message: [____________]
            [____________]
            [____________]

   [Send Message]
   ```

4. **Response Time**
   ```
   We typically respond within 24 hours.
   Premium and Pro users get priority support.
   ```

---

## Technical Requirements

### Performance
- Lighthouse score > 90 (all categories)
- First Contentful Paint < 1.5s
- Largest Contentful Paint < 2.5s
- Cumulative Layout Shift < 0.1

### SEO
- Semantic HTML (h1, h2, nav, main, footer)
- Meta tags for each page
- Open Graph tags for social sharing
- Twitter Card tags
- Sitemap.xml
- robots.txt

### Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader friendly
- Color contrast ratios met
- Alt text for all images

### Security
- HTTPS only
- CSP headers
- No inline scripts
- Form validation (client + server)
- Rate limiting on contact form

---

## Assets Needed

### From Client
- [ ] Logo files (SVG, PNG)
- [ ] App screenshots (high-res)
- [ ] Notification examples
- [ ] Favicon / App icon
- [ ] Any existing brand assets

### To Create
- [ ] Hero illustrations/graphics
- [ ] Feature icons
- [ ] Social media preview images
- [ ] Pricing comparison graphics

---

## Deployment

### Netlify Configuration

```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = ".next"

[[redirects]]
  from = "/*"
  to = "/en/:splat"
  status = 302
  conditions = {Language = ["en"]}

[[redirects]]
  from = "/*"
  to = "/es/:splat"
  status = 302
  conditions = {Language = ["es"]}

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
```

### Environment Variables
```
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
CONTACT_FORM_ENDPOINT=https://...
```

---

## Timeline Estimate

| Phase | Tasks | Duration |
|-------|-------|----------|
| 1. Setup | Next.js, Tailwind, i18n, Netlify | 1 day |
| 2. Design System | Colors, typography, components | 1 day |
| 3. Pages | Home, Features, Download | 2 days |
| 4. Pages | Pricing, Contact | 1 day |
| 5. i18n | Spanish translations | 1 day |
| 6. Polish | Animations, responsive, testing | 1 day |
| 7. Launch | SEO, analytics, deploy | 1 day |
| **Total** | | **~8 days** |

---

## Success Metrics

- Download button clicks
- Free → Premium conversion rate
- Contact form submissions
- Bounce rate < 40%
- Average session duration > 2 min

---

## Questions for Client

1. Do you have existing logo files?
2. Do you have app screenshots ready?
3. What email should the contact form send to?
4. Do you want to integrate a payment processor (Stripe)?
5. Any specific testimonials or social proof to include?
6. Domain name for the website?

---

*Specification created: January 21, 2026*
*For: CushLabs.ai / StockAlert*
