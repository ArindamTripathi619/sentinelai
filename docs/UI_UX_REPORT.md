# SentinelAI — Frontend UI/UX Report

> Generated from source code analysis. Covers all 11 JSX components, CSS, Tailwind config, behavioral SDK, and API layer.

---

## Table of Contents

1. [Technology Stack](#1-technology-stack)
2. [Routing & Navigation Structure](#2-routing--navigation-structure)
3. [Global Theme & Layout Shell](#3-global-theme--layout-shell)
4. [Login Page (`/login`)](#4-login-page-login)
5. [Register Page (`/register`)](#5-register-page-register)
6. [Forgot Password Page (`/forgot-password`)](#6-forgot-password-page-forgot-password)
7. [Reset Password Page (`/reset-password?token=...`)](#7-reset-password-page-reset-password)
8. [Events Page (`/events`)](#8-events-page-events)
9. [Dashboard — Command Center (`/dashboard`)](#9-dashboard--command-center-dashboard)
10. [User Timeline (`/dashboard/users/:userId/timeline`)](#10-user-timeline-dashboardusersuseridtimeline)
11. [Behavioral Fingerprinting SDK](#11-behavioral-fingerprinting-sdk)
12. [API Layer & Auth Utilities](#12-api-layer--auth-utilities)
13. [Error & Loading States (Cross-Cutting)](#13-error--loading-states-cross-cutting)
14. [Responsive Behavior Summary](#14-responsive-behavior-summary)

---

## 1. Technology Stack

| Concern | Choice |
|---------|--------|
| Framework | React 18.2 + Vite 5.2 |
| Routing | react-router-dom v6.22 |
| Styling | Tailwind CSS 3.4 with extensive custom theme (`cyber` colors, fonts, animations, shadows, bg images) |
| Icons | lucide-react v0.364 |
| Charts | recharts v2.12 (LineChart, PieChart) |
| HTTP | axios v1.6.8 |
| No TypeScript | All JSX files are plain JSX |
| Port | Dev server on `:3000` |
| API Base | `VITE_API_BASE_URL` env var, default `http://localhost:9000/api` |
| Source layout | `src/auth/` (5 components), `src/dashboard/` (3 components), `src/lib/`, `src/sdk/` |

---

## 2. Routing & Navigation Structure

Defined in `App.jsx`. The router uses `BrowserRouter` with these routes:

```
/                               → RootRedirect (automatic redirect)
/login                          → Login
/register                       → Register
/forgot-password                → ForgotPassword
/reset-password                 → ResetPassword
/events                         → ProtectedRoute → EventsPage
/dashboard                      → ProtectedRoute → AdminGuard → Dashboard
/dashboard/users/:userId/timeline → ProtectedRoute → AdminGuard → UserTimeline (page mode)
```

**Redirect logic (`RootRedirect`):**
- No token → `/login`
- Has token, `isAdmin()` → `/dashboard`
- Has token, not admin → `/events`

**ProtectedRoute** wraps children; state-driven with `storage` event listener for cross-tab sync. Redirects to `/login` if no token.

**AdminGuard** checks token + JWT `is_admin` claim + token expiry. Listens for `storage` events (cross-tab logout). Shows a centered spinner during check. Redirects non-admin users to `/events`, unauthenticated to `/login?error=unauthorized`.

---

## 3. Global Theme & Layout Shell

### 3.1 Tailwind Configuration (`tailwind.config.js`)
- **Custom theme extensions** — full cyber design system:

**Font families:**
| Alias | Font | Usage |
|-------|------|-------|
| `heading` | Syne | Page titles, prominent text |
| `headline` | Public Sans | Alternate headlines |
| `body` / `sans` | DM Sans | Body copy, form labels |
| `label` | DM Sans | Badge labels |
| `mono` | JetBrains Mono | Timestamps, IPs, JSON |

**Custom colors (`cyber.*`)**
| Token | Hex | Role |
|-------|-----|------|
| `cyber.black` | `#0a0a0f` | Page bg, sidebar |
| `cyber.dark` | `#0f0f1a` | Alt dark bg |
| `cyber.deeper` | `#07070d` | Input fields |
| `cyber.surface` | `#14142a` | Card surface |
| `cyber.card` | `#1a1a2e` | Card backgrounds |
| `cyber.border` | `#2a2a4a` | Borders |
| `cyber.cyan` | `#00f0ff` | Primary interactive (equivalent to `primary`) |
| `cyber.magenta` | `#ff00e4` | Accent (alerts, timeline) |
| `cyber.amber` | `#ffbf00` | Warnings |
| `cyber.red` | `#ff3355` | Critical/errors |
| `cyber.green` | `#00ff87` | Safe/success |

Top-level aliases: `primary`→`#00f0ff`, `accent`→`#ff00e4`, `warning`→`#ffbf00`, `critical`→`#ff3355`, `safe`→`#00ff87`, `surface`→`#0a0a0f`, `panel`→`rgba(10,10,15,0.8)`.

**Custom animations:** `pulse-glow`, `scan-line`, `data-stream`, `float`, `scanline`

**Custom background images:** `cyber-grid` (dot grid), `cyber-gradient` (cyan→magenta), `glass` (subtle white gradient)

**Custom shadows:** `neon-cyan` (0 0 15px + 45px), `neon-magenta`, `glass`

### 3.2 Base CSS (`index.css` — 120 lines)

**@layer base:**
```css
body {
  @apply bg-surface text-white antialiased;
  font-family: 'DM Sans', system-ui, sans-serif;
}
```
Custom scrollbar styling (6px wide, `#07070d` track, `#2a2a4a` thumb, cyan on hover).

**@layer components — custom utility classes:**

| Class | Effect |
|-------|--------|
| `.glass-card` | `bg-[#1a1a2e]/40`, `backdrop-blur-xl`, `border-[#2a2a4a]/50`, `shadow-glass` |
| `.glass-card-strong` | More opaque variant (60% bg) |
| `.glass-panel` | `rgba(10,10,15,0.8)` bg, cyan-tinted border + inset glow |
| `.scanline-overlay` | 4px CRT scanline pattern at 2% opacity |
| `.input-cyber` | Dark input with cyan focus ring |
| `.input-cyber-icon` | Same with `pl-10` for icon inset |
| `.btn-cyber-primary` | Cyan-filled button with hover overlay |
| `.badge-cyber` / `.badge-cyan` / `.badge-magenta` / `.badge-amber` / `.badge-red` / `.badge-green` | Themed badges |

**@layer utilities:**
- `.bg-cyber-grid-overlay` — 60px cyan dot grid
- `.text-glow-cyan` — cyan text-shadow (10px + 30px)
- `.text-glow-magenta` — magenta text-shadow

### 3.3 Entry Point (`index.html`)
```html
<title>SentinelAI — Command Center</title>
```
Google Fonts loaded: Syne (400–800), DM Sans (300–700), JetBrains Mono (400–700). No `bg-gray-900` class on `<body>` — background handled by React's `bg-surface` on each page wrapper.

---

## 4. Login Page (`/login`)

**File:** `src/auth/Login.jsx` (351 lines)

### 4.1 Page Layout
- `min-h-screen bg-surface text-slate-300 font-body flex flex-col overflow-hidden`
- Full-viewport cyber aesthetic with layered background effects
- `selection:bg-primary/30` custom selection color

### 4.2 Background Design
Three fixed layers (`z-0`, `pointer-events-none`):
1. **Radial gradient glow** — `radial-gradient(ellipse_at_center, rgba(0,240,255,0.08) 0%, transparent 70%)` centered cyan ambient light
2. **Decorative border ring** — `absolute inset-4 border border-primary/5 rounded-[4rem] opacity-40`
3. **Scanline overlay** — `.scanline-overlay opacity-20` (CRT 4px line pattern)

### 4.3 Corner Status Indicators (hidden below `lg`, `pointer-events-none`)
```
Top-left:
  System_Status: Operational
  Node: HQ_WEST_04
  {currentTime} UTC          ← updates every 1s via setInterval

Top-right:
  CLEARANCE: LEVEL_0
  CONN: ENCRYPTED
  PROTO: TLS_1.3
```
Both use `font-headline text-[10px] text-primary/40`.

### 4.4 Login Card (`.glass-panel`)
- **Dimensions:** `w-full max-w-md`
- **Container:** `.glass-panel` — `rgba(10,10,15,0.8)` bg, `backdrop-filter: blur(12px)`, cyan-tinted border, inset glow shadow
- **Top accent:** `border-t-2 border-primary/50`
- **Animated glow line:** absolute positioned `h-px w-3/4` gradient from transparent → `#00f0ff` → transparent at top center, with `shadow-[0_0_15px_#00f0ff]`
- **Padding:** `p-8`, **radius:** `rounded-lg`
- **Inner layout:** `flex flex-col items-center`

### 4.5 Logo / Brand Area
```
Shield icon:
  w-16 h-16 rounded-full border border-primary/30 bg-primary/5
  Shield icon (w-8 h-8 text-primary)
  Pulsing ring: absolute inset-0 rounded-full border border-primary/20 animate-ping opacity-20

Title: "SENTINELAI"
  font-headline text-3xl font-black tracking-tighter uppercase italic
  "AI" in text-primary italic
Subtitle: "CYBER COMMAND LOGIN" — font-label text-xs tracking-widest text-primary/60 uppercase
Tagline: "Biometric handshake required for level 5 access." — text-[10px] text-slate-500
```

### 4.6 Form Fields (cyber aesthetic)

**Email field ("Access_Identifier"):**
- Label: `text-[10px] font-bold text-slate-500 tracking-[0.2em] uppercase` — "Access_Identifier"
- Container: `relative group`
- Icon: `Mail` (w-4 h-4), `text-slate-500`, turns `group-focus-within:text-primary`
- Input: `w-full bg-black/40 border-slate-800 rounded-lg py-3 pl-10 pr-4 text-sm text-white placeholder:text-slate-700 focus:outline-none focus:border-primary`
- Placeholder: `OPERATOR@SENTINEL.AI`

**Password field ("Passphrase_Key"):**
- Label same style — "Passphrase_Key"
- "Recover?" link (right-aligned): `text-[9px] text-primary/60 hover:text-primary uppercase` → `/forgot-password`
- `Lock` icon, same input styling
- Placeholder: `••••••••••••`

### 4.7 Submit Button ("Authenticate")
```
Background: bg-primary hover:bg-primary/90
Text:       text-black font-black uppercase tracking-widest text-xs
Padding:    py-4
Width:      w-full
Radius:     rounded
Effects:    shadow-[0_0_20px_rgba(0,240,255,0.4)]
            hover:shadow-[0_0_30px_rgba(0,240,255,0.6)]
            active:scale-95
```
**Content when idle:** "Authenticate" + `ArrowRight` (w-3.5 h-3.5)
**Content when loading:** Spinning loader — `w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin`

### 4.8 Navigation
- "Request Clearance / Register Account" link at card bottom: `UserPlus` icon, `text-[10px] text-slate-500 hover:text-primary` → `/register`

### 4.9 OTP Verification Sub-form
Triggered by `otp_required` response. Replaces login form:
- `KeyRound` icon (w-10 h-10, text-primary)
- Title: "MFA_AUTHENTICATION" — `font-headline font-bold text-lg text-white`
- Subtitle: "Enter the 6-digit code sent to your session"
- Input: `text-center text-lg font-mono tracking-[0.4em]`, placeholder `123456`, `maxLength={6}`, `inputMode="numeric"`
- Button: same cyan primary style, text "Verify OTP" + `ArrowRight`
- "Back to login" link — resets `requiresOtp` to false

### 4.10 CAPTCHA Verification Sub-form
Triggered by `captcha_required` response:
- `Shuffle` icon (w-10 h-10, `text-warning`)
- Title: "Security Check"
- CAPTCHA prompt display: `bg-black/40 border-slate-800 tracking-[0.5em] text-xl font-mono text-warning`
- Answer input: `text-center uppercase font-mono tracking-[0.3em]`, placeholder "Enter code"
- Button: `bg-warning` style with amber glow shadow, text "Verify" + `ArrowRight`
- "Back to login" link

### 4.11 Error / Info Banners
- **Error:** `rounded-lg border border-critical/30 bg-critical/10 px-4 py-3 text-sm text-critical` with pulsing red dot
- **Info:** `rounded-lg border border-primary/30 bg-primary/10 px-4 py-3 text-sm text-primary` with pulsing cyan dot

### 4.12 Behavioral Profiling Footer
```
Fixed bottom section, space-y-3:
  Live dot with animate-ping, bg-safe
  "BEHAVIORAL PROFILING ACTIVE" — text-[10px] font-bold uppercase tracking-[0.2em]
  "Encrypted Connection: SHA-512_RSA_2048"
  Status row: "SEC_INIT: OK" | "NET: SECURE_TUNNEL" | "NODE_SYNC: ACTIVE"
  Boot sequence text: AES-256_GCM_INIT • TLS_1.3_HANDSHAKE • SECURE_CHANNEL_ESTABLISHED...
```

### 4.13 Form Submission
Sends `POST /login` with `email`, `password`, `behavioralData`, `user_agent: navigator.userAgent`.

Response handling order:
1. `otp_required` → OTP sub-form, auto-sends `POST /otp/send` with session ID + email
2. `captcha_required` → CAPTCHA sub-form with `captcha_token`, `captcha_prompt`
3. `is_blocked` → Shows `response.data.message` as error
4. `token` present → Stores session, navigates admin → `/dashboard`, non-admin → `/events`

---

## 5. Register Page (`/register`)

**File:** `src/auth/Register.jsx` (269 lines)

### 5.1 Layout & Background
Same structural pattern as Login:
- `min-h-screen bg-surface text-slate-300 font-body flex flex-col overflow-hidden`
- Same 3-layer background: cyan radial gradient + scanline overlay + corner status indicators
- Corner status: "SYS_INIT: OK" / "NET_STATUS: ENCRYPTED" / "MODE: REGISTRATION_GATE"
- Card: same `.glass-panel` with `border-t-2 border-primary/50` and animated glow line

### 5.2 Visual Identity
- Same `Shield` icon (w-8 h-8) in pulsing ring container
- **Title:** "SENTINELAI" — `font-headline text-3xl font-black tracking-tighter uppercase italic`
- **Subtitle:** "Create Your Account" — `font-label text-xs tracking-widest text-primary/60 uppercase`

### 5.3 Form Fields (5 fields)

**Full Name:** `User` icon, placeholder `Full Name`. When filled: border turns `border-safe/50`, `CheckCircle` icon appears (w-3.5 h-3.5, `text-safe`), label turns `text-safe/60`.

**Email Address:** `Mail` icon, placeholder `Email Address`

**Organization / Entity:** `Building2` icon, placeholder `Organization / Entity`

**Password:** `Lock` icon, show/hide toggle (`Eye`/`EyeOff`). Below input:

**Password strength meter** (shown when field non-empty):
- 4-segment bar (`h-1 rounded-full`), each segment fills progressively
- Color: `bg-critical` (1-2), `bg-warning` (3), `bg-safe` (4-5)
- Max segments glow: `shadow-[0_0_8px_#00ff87]` on safe level
- Labels: "Entropy: {None/Weak/Fair/Moderate/Maximum/Maximum}" + "Security Level: {—/Level 0-4}"
- Scoring: +1 each for ≥8 chars, ≥12 chars, has uppercase, has digit, has special char

**Confirm Password:**
- `Lock` icon, same input styling
- Border turns `border-critical/50` when mismatch
- Inline error: "Authentication mismatch: Passwords must align." — `text-[10px] text-critical`

### 5.4 Submit Button
Same cyan primary style as Login: `bg-primary text-black font-black uppercase tracking-widest text-xs py-4 rounded shadow-[0_0_20px_rgba(0,240,255,0.4)]`
**Text:** "REGISTER ACCOUNT"
**Loading:** Spinning spinner

### 5.5 Success & Error Handling
- **Error:** Red banner with pulsing dot — `border-critical/30 bg-critical/10 text-critical`
- **Success:** Green banner with `CheckCircle` — `border-safe/30 bg-safe/10 text-safe`, shows trust score. Auto-redirects to `/login` after 1200ms.

### 5.6 Navigation
`"Already have an account? Log In"` — `text-[10px] uppercase tracking-wider text-slate-500`

### 5.7 Footer
Same behavioral profiling indicator as Login: green ping dot + "BEHAVIORAL PROFILING ACTIVE" + links (Terms of Service, Privacy Protocol, System Status).

---

## 6. Forgot Password Page (`/forgot-password`)

**File:** `src/auth/ForgotPassword.jsx` (148 lines)

### 6.1 Layout
- `min-h-screen bg-surface text-slate-200 font-body flex flex-col items-center justify-center overflow-hidden`
- Background: cyan radial gradient `rgba(0,240,255,0.06)` at center + vignette overlay `radial-gradient(circle_at_center, transparent 0%, rgba(0,0,0,0.4) 100%)`
- Corner status (LG only): left → "System_Status: Standby / Node: AUTH_GATE_02", right → "CLEARANCE: LEVEL_0 / CONN: ENCRYPTED / PROTO: TLS_1.3"
- Card: `.glass-panel` with cyan border-top + animated glow line
- Same `Shield` icon with pulsing ring, "SENTINELAI" brand, subtitle "RESET PASSWORD"

### 6.2 Form
- Label: "OPERATOR_EMAIL" — `text-[10px] font-bold text-slate-500 tracking-[0.2em]`
- Input: `block w-full pl-10 pr-4 py-3 bg-slate-950/60 border border-slate-800 focus:border-primary focus:ring-1 focus:ring-primary/20 text-primary placeholder:text-slate-700 text-sm`
- Placeholder: `OPERATOR@SENTINEL.AI`
- `Mail` icon: `text-primary/40 group-focus-within:text-primary`
- Button: "SEND RESET LINK" — `w-full py-4 bg-primary text-slate-950 font-black tracking-widest text-xs uppercase hover:shadow-[0_0_20px_rgba(0,240,255,0.4)] active:scale-[0.98]`
- Footer link: "Back to Command Center Login" — `text-[10px] font-bold tracking-widest text-slate-500 hover:text-primary uppercase border-b border-transparent hover:border-primary/50`

### 6.3 Post-submit State
Replaces form with success view:
- **CheckCircle icon:** `w-16 h-16 bg-safe/20 blur-xl` glow behind `bg-safe/10 ring-1 ring-safe/40` container
- **Text:** "Check your email" — `text-safe font-medium text-sm`
- **Detail:** "If that email is registered, we've sent a password reset link."
- **Link:** "Back to Command Center Login" with `ArrowLeft`

### 6.4 Footer
Fixed bottom `bg-surface/60 backdrop-blur-sm border border-slate-800/50` bar with green ping dot + "BEHAVIORAL PROFILING ACTIVE"

---

## 7. Reset Password Page (`/reset-password`)

**File:** `src/auth/ResetPassword.jsx` (205 lines)

### 7.1 Token Validation
Reads `token` from `?token=` search param. If no token:
- Standalone error UI inside `.glass-panel`: "Invalid reset link. No token provided."
- Link: "Request a new reset link" with `ArrowLeft` → `/forgot-password`

### 7.2 Layout (with valid token)
- Same background as ForgotPassword: cyan gradient + vignette
- Corner status (LG only): "SEC_LEVEL: 04 / ENCR: AES_256 / STAT: TOKEN_ACCEPTED"
- Card: `.glass-panel p-8 md:p-10 flex flex-col items-center space-y-8`
- `KeyRound` icon (w-8 h-8) with `bg-primary/20 blur-xl` glow background
- Title: "SENTINEL AI" + "SET NEW PASSWORD"

### 7.3 Form Fields

**New Password ("NEW PASSPHRASE"):**
- `Lock` icon (w-4 h-4), placeholder `••••••••••••`, `minLength={8}`
- Input: `block w-full pl-10 pr-10 py-3 bg-slate-950/60 border border-slate-800 focus:border-primary text-primary placeholder:text-slate-700 text-sm`
- Show/hide toggle button: `Eye`/`EyeOff` icons, `text-slate-600 hover:text-white`

**Confirm Password ("CONFIRM PASSPHRASE"):**
- Same styling, with conditional `border-critical/50` on mismatch
- Inline error: "Authentication mismatch: Passwords must align." — `text-[10px] text-critical`

### 7.4 Submit & Validation
Client-side checks before API call:
1. Passwords must match ("Authentication mismatch: Passwords must align.")
2. Password length >= 8 ("Password must be at least 8 characters.")

Button: "Reset Password" + `Shield` icon — `bg-primary text-slate-950 font-black tracking-widest text-xs uppercase hover:shadow-[0_0_20px_rgba(0,240,255,0.4)]`

### 7.5 Post-submit State
- Same `CheckCircle` with safe glow pattern
- Text: "Password reset successful"
- Detail: "You can now log in with your new password."
- Button: "Go to Login" — full-width cyan primary style, navigates to `/login`

### 7.6 Footer
Same fixed behavioral profiling bar as ForgotPassword.

---

## 8. Events Page (`/events`)

**File:** `src/auth/Events.jsx` (50 lines)

### 8.1 Current State
**Placeholder** — cyber styled:
- Full `bg-surface` with cyan radial gradient + `.scanline-overlay`
- Center `.glass-panel` with `Activity` icon in warning-colored container (`bg-warning/10 ring-1 ring-warning/30`)
- Title: "Event Platform" — `text-xl font-headline font-bold text-white`
- Text: "Event listing — under construction"
- Note: "Event management features coming soon."

### 8.2 Actions
- **Admin users:** "Back to Dashboard" button — `border border-primary/30 text-primary hover:bg-primary/10` → `/dashboard`
- **All users:** "Logout" button — `border border-slate-800/50 text-slate-400 hover:text-critical hover:border-critical/30`

### 8.3 Intended Use
Landing page for non-admin authenticated users. Event listing not yet implemented.

---

## 9. Dashboard — Command Center (`/dashboard`)

**File:** `src/dashboard/Dashboard.jsx` (686 lines)

The primary admin interface — a full command center with sidebar nav, pinned header, 4 KPI cards, velocity chart, trust distribution donut, paginated users table, and live alerts panel. All data polls every **4 seconds**.

### 9.0 Layout Structure
```
┌─────────────────────────────────────────────────────┐
│ Sidebar (w-56)  │  Header (fixed, h-14)            │
│                 ├───────────────────────────────────┤
│ SENTNEL_AI      │  main (ml-56, pt-20, px-6, pb-10)│
│ [nav items]     │  ┌─ KPI Cards (4-col grid) ────┐ │
│                 │  ├─ Velocity Chart (8-col)      │ │
│ INITIATE SCAN   │  │  Trust Donut (4-col)        │ │
│ [admin badge]   │  ├─ Users Table (8-col)        │ │
│ Logout          │  │  Active Alerts (4-col)       │ │
└─────────────────┴───────────────────────────────────┘
```

### 9.1 Sidebar (`w-56 fixed left-0 h-screen`)
- Background: `bg-[#0a0a0f]/80 backdrop-blur-md border-r border-primary/20`
- **Logo:** "SENTNEL_AI" — `font-headline font-black tracking-widest text-primary` with `drop-shadow-[0_0_8px_rgba(0,240,255,0.6)]`
- **Version:** "V_2.0.4 STATUS: ACTIVE" — `text-[10px] text-slate-500`

**Navigation items** (6 buttons):
| ID | Label | Icon | Route |
|----|-------|------|-------|
| dashboard | Command Center | `LayoutDashboard` | `/dashboard` |
| users | Users | `Users` | — |
| timeline | Timeline | `Clock` | — |
| events | Events | `Activity` | `/events` |
| alerts | Alerts | `Bell` | — |
| settings | Settings | `Settings` | — |

- Active state: cyan left border (4px) + `bg-gradient-to-r from-primary/10 to-transparent text-primary`
- Inactive: `text-slate-400 hover:bg-primary/5 hover:text-primary`

**Bottom section:**
- "INITIATE SCAN" button: `bg-transparent border border-primary/40 text-primary font-headline text-[10px] tracking-widest hover:bg-primary hover:text-surface`
- Admin badge: shield icon in `border border-primary/30 bg-primary/5`, green dot (`bg-safe rounded-full border-2 border-surface`)
- Admin email: from JWT payload `email` field (before `@`, uppercased)
- Security clearance: derived from avg trust score `Math.min(5, Math.max(1, Math.round(avg_trust_score / 20)))`
- "Security Log" and "Logout" links

### 9.2 Header (`fixed top-0 right-0 left-56 h-14`)
- Background: `bg-[#0a0a0f]/60 backdrop-blur-xl border-b border-primary/20`
- **Left:** "Command Center" title + "LIVE" badge with green ping dot
- **Search:** `w-56` input with `Search` icon, debounced 300ms, placeholder "SEARCH USERS BY EMAIL..."
- **Tabs:** "LIVE_FEED" (active, cyan underline) | "NETWORK_MAP" (inactive)
- **Right icons:** `Bell` (with accent dot), `Terminal`, `GitBranch`, divider, UTC clock (1s interval)

### 9.3 KPI Cards (4-column grid)
**Grid:** `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5`

4 cards from `/analytics/summary`:

| Card | Value Field | Icon | Extra |
|------|-------------|------|-------|
| Total Users | `summary.total_users` | `Users` | Ghost icon in bg corner |
| Avg Trust Score | `summary.avg_trust_score` | `Shield` | SVG ring gauge (radius 16, stroke 4, cyan) with percentage center |
| Active Alerts | `summary.active_alerts` | `Activity` | Red border tint (`border-critical/30`) |
| Threats Detected | `summary.flagged_today` | `ShieldAlert` | Red border tint |

**Loading state:** `inline-block w-12 h-6 bg-slate-800/60 rounded animate-pulse` skeleton
**Ring gauge:** SVG circle with `strokeDasharray="100.5"`, `strokeDashoffset` computed from score, `strokeLinecap="round"`, center text `text-[9px] font-bold text-primary`

### 9.4 Main Grid (12-column)
**Grid:** `grid grid-cols-12 gap-6`

#### Panel A: Request Velocity Chart (spans 8)
- `.glass-panel p-5`
- Header: `Activity` icon + "Request Velocity" title
- **Time window buttons:**
  | Button | Key | Bucket |
  |--------|-----|--------|
  | 1H | `1h` | `1min` |
  | 6H | `6h` | `5min` |
  | 24H | `24h` | `30min` |
  | 7D | `7d` | `1h` |
  - Active: `border-primary text-primary bg-primary/10`
- **Recharts LineChart** in `ResponsiveContainer h-56`:
  - `CartesianGrid`: `stroke="rgba(255,255,255,0.04)` dotted, no vertical
  - X/YAxis: `stroke="#475569"`, no axis/tick line, `fontSize={9}`
  - Tooltip: dark theme `bg-[#0a0a0f] border border-primary/20`
  - Line: `stroke="#00f0ff"`, `strokeWidth={2}`, `dot={false}`, cyan gradient fill area
  - Data mapped: `time` (HH:MM) vs `signups` (registrations)
  - Fallback: `['T1', 'T2', ...]` if no timestamps
- **Floating overlay** at top-center: `bg-surface/80 border border-primary/40` showing timestamp and "REQ_VOL: X/SEC"

#### Panel B: Trust Distribution Donut (spans 4)
- `.glass-panel p-5`
- Header: `Activity` icon + "Trust Distribution"
- **Recharts PieChart** in `w-44 h-44`:
  - `innerRadius={32}`, `outerRadius={52}`, no padding
  - Colors: `['#00f0ff', '#00ff87', '#ffbf00', '#ff3355', '#cc0044']`
  - Tooltip: dark style, formatter `"${value} nodes"`
  - Center overlay: total count + "TOTAL_NODES" label
- **Legend grid** (2-column): color dot + label + percentage
- **Edge case:** empty → fallback gray `[{ label: 'No data', count: 1, color: '#1a1a2e' }]`

#### Panel C: Recent Users Table (spans 8)
- `.glass-panel overflow-hidden`
- Header: `Users` icon + "Recent Users" title + "Export CSV" button
- **Table columns:**
  | Column | Content |
  |--------|---------|
  | User Identity | Initials badge (w-7 h-7, 2-char from email) + username (clean) + email |
  | Trust Score | `{score}/100` — green (≥70), amber (≥40), red (<40) |
  | Risk Profile | Badge: CRIT (<20), HIGH (<40), MED (<70), LOW (70+) |
  | Activity | Relative time: "Just now", "Xm ago", "Xh ago", "Xd ago" |
  | Status | Colored dot + badge: AUTHORIZED (green), CHALLENGED (amber), QUARANTINED/BLOCKED (red). Ping on <20 |
  | Action | `Eye` icon button → `/dashboard/users/:userId/timeline` |
- **Search** filters via `?q=` param, debounced 300ms, resets to page 1
- **Pagination:** Prev/Next + up to 5 page number buttons with sliding window, "X–Y of Z" summary
- **Export CSV:** generates blob with headers `Email,Trust Score,Status,Last Activity`, download `sentinelai_users_export.csv`
- **Empty state:** "No users match your search."

#### Panel D: Active Alerts (spans 4)
- `.glass-panel p-5`
- Header: `Bell` icon + "Active Alerts" + NEW count badge (`bg-accent/10 text-accent`)
- Data from `/alerts?limit=15`
- **Alert cards** per type:
  | Type | Icon | Color |
  |------|------|-------|
  | `bot_wave` | `Zap` | Magenta (`bg-accent/5`) |
  | `geo_drift` | `Globe` | Amber (`bg-warning/5`) |
  | `speed_bot` | `Zap` | Red (`bg-critical/5`) |
  | `duplicate_device` | `Activity` | Magenta |
  | `email_pattern` | `Shield` | Amber |
  | `velocity_spike` | `TrendingUp` | Red |
- Actions: "Deploy Firewall" (bot_wave) or "Investigate" + "Dismiss" → PATCH `/alerts/:id/resolve`
- **Empty state:** "No active alerts"

### 9.5 Polling
- Initial mount + recursive `setTimeout` every **4 seconds** (waits for completion before scheduling next)
- 5 parallel requests: summary, velocity, trust-distribution, users, alerts
- 401 → clear session + redirect to `/login`
- `mounted` flag + `clearTimeout` cleanup

---

## 10. User Timeline (`/dashboard/users/:userId/timeline`)

**File:** `src/dashboard/UserTimeline.jsx` (451 lines)

### 10.1 Dual Mode
Controls via `mode` prop:

**Modal mode (`mode="modal"`, default):**
- Overlay: `fixed inset-0 bg-surface/80 backdrop-blur-sm flex items-center justify-center z-50 p-4`
- Panel: `.glass-panel max-w-3xl w-full max-h-[90vh] overflow-hidden`
- Header: "Forensic Replay" — `History` icon, close `X` button
- Simpler event cards (no vertical timeline, no country badge, no metadata expand)

**Page mode (`mode="page"`):**
- Full-page layout: `min-h-screen bg-surface flex font-body text-slate-300`
- **Sidebar** (w-56): "SENTNEL_AI" brand, 5 nav items (Timeline highlighted with accent), "Dashboard" back button (w/ `ArrowLeft`)
- **Main area:** `flex-1 overflow-y-auto`
- **Sticky header:** breadcrumb "Dashboard → User Timeline", "User Investigation" title, user email
- **User summary card** inside `.glass-panel`: trust score (colored), risk level badge, total events, filtered count — data from `GET /users/:userId`

### 10.2 Filter Controls (page mode, inside `.glass-panel`)
**Header:** `Filter` icon + "Timeline Filters" + **Export CSV** button

**Export CSV:** generates `sentinelai-timeline-{userId}.csv` with columns: timestamp, action, description, trust_score, country, ip_address, user_agent, metadata. `escapeCsv` handles quotes/commas/newlines.

**3 dropdown filters** (`grid gap-3 md:grid-cols-3`):
| Filter | Options |
|--------|---------|
| Action Type | All, Register, Login, Login Failed, OTP sent, OTP verified, CAPTCHA verified, Quarantined, Geo Drift, Blocked |
| Time Window | All time, Last 24h, Last 7d, Last 30d |
| Trust Band | All, Critical (<20), Elevated (20-39), Moderate (40-69), Safe (70+) |

**Reset filters** link clears all to "all"

### 10.3 Filter Logic (client-side)
1. **Action filter:** `event.action_type || event.action` lowercase match
2. **Trust band:** `<20`→high, `20-39`→medium, `40-69`→low, `70+`→safe
3. **Time window:** cutoff from now (86400000 / 604800000 / 2592000000 ms)

### 10.4 Timeline Events (page mode)
- Vertical timeline: `absolute left-4 top-0 bottom-0 w-px bg-gradient-to-b from-accent/40 via-primary/20 to-transparent`
- Each event: accent dot (`w-2 h-2 rounded-full bg-accent ring-2 ring-surface`) + `.glass-panel` card
- **Action badge:** color-coded by type:
  - `register`: `text-primary border-primary/30 bg-primary/10`
  - `login`: `text-safe border-safe/30 bg-safe/10`
  - `login_failed`: `text-critical border-critical/30 bg-critical/10`
  - `otp_sent`/`otp_verified`: `text-primary border-primary/30 bg-primary/10`
  - `captcha_verified`: `text-warning border-warning/30 bg-warning/10`
  - `blocked`/`flagged`: `text-critical border-critical/30 bg-critical/10`
  - `quarantined`: `text-amber border-amber/30 bg-amber/10`
  - `geo_drift`: `text-accent border-accent/30 bg-accent/10`
- **Trust score:** color by band (`<20` critical, `<40` warning, `<70` warning, `70+` safe)
- **Country badge** when present
- **Metadata section:** collapsible `JSON.stringify` in `<pre>` monospace block (text-[9px])
- Info grid: timestamp (`Clock`), IP (`MapPin`), user agent (`Zap`)

### 10.5 Indicators / Empty / Loading / Error States
- **User summary:** shows trust score (colored) + risk level badge (CRITICAL/HIGH/ELEVATED/LOW) from `getUserDetail`, fallback "Loading..." or "Pending"
- **Loading:** centered `Loader` (w-8 h-8, text-primary, animate-spin) in h-64
- **Error:** red banner with `AlertCircle` — `bg-critical/10 border border-critical/30`
- **Empty results:** `Clock` icon (w-8 h-8 opacity-50) + "No activity matches the current filters"

---

## 11. Behavioral Fingerprinting SDK

**File:** `src/sdk/behavioral.js` (204 lines)

Used in both `Login.jsx` and `Register.jsx`:
```js
const getBehavioralPayload = useBehavioral();
// on submit: const behavioralData = getBehavioralPayload();
```

### 11.1 Tracking Architecture
- `startTracking()` on mount, `stopTracking()` on unmount
- `useBehavioral()` React hook auto-calls `startTracking()` if `window` is defined, returns `getPayload`
- All signals collected client-side, sent as `behavioralData` with form submissions

### 11.2 Signals Collected

| Signal | Description | Collection Method |
|--------|-------------|-------------------|
| `typing_variance_ms` | Standard deviation of inter-keypress intervals (ms) | `keydown` listener → timestamps → stddev |
| `time_to_complete_sec` | Total time from start to submission (seconds) | Delta between `startTracking` and `getPayload` |
| `session_tempo_sec` | Mean interval between all interactions (seconds) | Combined key/mouse/focus timestamps → average |
| `mouse_entropy_score` | Directional entropy of mouse movements (0-1) | Throttled mousemove → direction buckets → Shannon entropy |
| `fill_order_score` | Naturalness of form field focus order (0-1) | `focusin` → field sequence → uniqueness/repetition ratio |
| `mouse_move_count` | Throttled count | 100ms throttle |
| `keypress_count` | Raw count | Every keydown |

### 11.3 Demo Override
`window.__DEMO_OVERRIDE__` — bypasses tracking, returns override directly. For presentations.

---

## 12. API Layer & Auth Utilities

**File:** `api.js` (57 lines)

### 12.1 Axios Instance
- Base URL from `VITE_API_BASE_URL` env var, fallback `http://localhost:9000/api`
- Default content-type: `application/json`
- Request interceptor attaches `Authorization: Bearer <token>` from localStorage when available

### 12.2 localStorage Keys
| Key | Purpose |
|-----|---------|
| `sentinelai_token` | JWT token |
| `sentinelai_user_id` | Current user UUID |

### 12.3 Auth Functions
- `getAuthToken()` / `setAuthToken(token)` / `clearUserSession()`
- `setUserSession({ token, userId })` — stores both
- `isAdmin()` — decodes JWT payload (base64 `atob` split on `.`), checks `payload.is_admin == true`
- Response interceptor catches 401 errors → clears session → redirects to `/login`

---

## 13. Error & Loading States (Cross-Cutting)

### 13.1 Error Banners (consistent pattern across all forms)
```
rounded-lg border border-{color}/30 bg-{color}/10 px-4 py-3 text-sm text-{color}
```
Uses custom palette:
- `critical` (`#ff3355`): Errors — with pulsing red dot
- `primary` (`#00f0ff`): Info messages (OTP/CAPTCHA prompts) — with pulsing cyan dot
- `safe` (`#00ff87`): Success messages — with `CheckCircle` icon

### 13.2 Loading Spinner (consistent pattern across buttons)
```
w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin
```
On cyan primary buttons: black spinner against cyan background.
On amber CAPTCHA buttons: black spinner against amber background.

### 13.3 Dashboard Loading
KPI cards show pulsing skeleton: `inline-block w-12 h-6 bg-slate-800/60 rounded animate-pulse`. Charts render empty until data arrives.

### 13.4 AdminGuard Loading
`min-h-screen bg-surface flex items-center justify-center` with `Shield` icon (w-8 h-8, `animate-pulse-glow`) + spinner.

---

## 14. Responsive Behavior Summary

All responsive breakpoints use Tailwind defaults:
- **`md:` breakpoint** (768px): KPI cards `md:grid-cols-2`, timeline filter `md:grid-cols-3`
- **`lg:` breakpoint** (1024px): KPI cards `lg:grid-cols-4`, main grid `lg:grid-cols-12` (8+4 split), sidebar/corner status visible

**Mobile layout (below md):**
- All charts, tables, and panels stack vertically (single column)
- Sidebar hidden (dashboard main area: `ml-56` → full width when sidebar hidden via media)
- Corner status indicators hidden (`hidden lg:block`)
- Tables horizontally scrollable (`overflow-x-auto`)
- Timeline modal approach for smaller containers

**Auth pages (all of them):**
- Always centered single-column (`max-w-md`)
- Cyber aesthetic maintained at all sizes

---

## Appendix A: Color Palette Summary

Custom `cyber.*` tokens (defined in `tailwind.config.js`):

| Token | Hex | Role |
|-------|-----|------|
| `cyber.black` / `surface` | `#0a0a0f` | Page backgrounds, sidebar |
| `cyber.dark` | `#0f0f1a` | Alternate dark bg |
| `cyber.deeper` | `#07070d` | Input fields |
| `cyber.surface` | `#14142a` | Card surface |
| `cyber.card` | `#1a1a2e` | Card bg, table rows |
| `cyber.border` | `#2a2a4a` | Borders |
| `cyber.cyan` / `primary` | `#00f0ff` | Interactive elements, links, focus rings |
| `cyber.magenta` / `accent` | `#ff00e4` | Alerts, timeline accent, notification dot |
| `cyber.amber` / `warning` | `#ffbf00` | Warnings, CAPTCHA flow, MED risk |
| `cyber.red` / `critical` | `#ff3355` | Errors, blocked status, CRIT risk |
| `cyber.green` / `safe` | `#00ff87` | Success, authorized status, LOW risk |
| `panel` | `rgba(10,10,15,0.8)` | Glass panel backgrounds |

Inline colors used:
- `slate-950` (#020617): Input backgrounds
- `slate-800` (#1e293b): Borders (auth), dividers
- `slate-500/600/700` (#64748b / #475569 / #334155): Secondary text, axes

## Appendix B: Chart and Graph Details

| Chart | Type | Library | Data Source | Refresh |
|-------|------|---------|-------------|---------|
| Request Velocity | Line (monotone) | recharts LineChart | `GET /analytics/velocity?window=1h&bucket=1min` (variable window/bucket) | Every 4s |
| Trust Distribution | Donut (Pie) | recharts PieChart | `GET /analytics/trust-distribution` | Every 4s |

## Appendix C: Typography Scale

| Element | Family | Size | Weight |
|---------|--------|------|--------|
| Dashboard title "SENTNEL_AI" | Syne (heading) | 1rem (16px) | 900 |
| Auth page title "SENTINELAI" | Syne (heading) | 1.875rem (30px) | 900 |
| Auth subtitles | DM Sans (label) | 0.75rem (12px) | 400 |
| KPI values | Syne (heading) | 1.5rem (24px) | 900 |
| KPI labels | DM Sans (body) | 0.625rem (10px) | 700 |
| Table header | DM Sans (body) | 0.625rem (10px) | 700 |
| Table cells | DM Sans (body) | 0.6875rem (11px) | 400 |
| Form labels | DM Sans (body) | 0.625rem (10px) | 700 |
| Submit buttons | DM Sans (body) | 0.75rem (12px) | 900 |
| Timeline action badges | DM Sans (body) | 0.5625rem (9px) | 700 |
| Corner status | Public Sans (headline) | 0.625rem (10px) | 400 |
| Behavioral footer | DM Sans | 0.625rem (10px) | 700 |
| Monospace data | JetBrains Mono | 0.625–0.75rem | 400 |

## Appendix D: Component Tree

```
<App>
  <BrowserRouter>
    <Routes>
      <Login />
      <Register />
      <ForgotPassword />
      <ResetPassword />
      <EventsPage />
      <ProtectedRoute>
        <AdminGuard>
          <Dashboard>                      (686 lines)
            ├── Sidebar (fixed, w-56)
            ├── Header (fixed, h-14)
            ├── KPI Cards (4×)
            │   └── Avg Trust Score: SVG ring gauge
            ├── Request Velocity           (Recharts LineChart)
            │   └── Time window buttons: 1H/6H/24H/7D
            ├── Trust Distribution         (Recharts PieChart donut)
            ├── Recent Users Table
            │   └── Pagination + CSV Export + Timeline eye btn
            └── Active Alerts Panel
                └── Dismiss via PATCH /alerts/:id/resolve
          </Dashboard>
        </AdminGuard>
        <AdminGuard>
          <UserTimeline>                  (451 lines)
            ├── Modal mode (default)
            │   └── Forensic Replay overlay
            └── Page mode
                ├── Sidebar + breadcrumb
                ├── User summary card (trust/risk)
                ├── 3-axis filter bar (action/time/trust)
                └── Vertical timeline + CSV Export
          </UserTimeline>
        </AdminGuard>
      </ProtectedRoute>
    </Routes>
  </BrowserRouter>
</App>
```

---

*Report generated from source analysis on 2026-06-17. Last updated after bug-fix pass: 30 bugs fixed across 14 files.*
*Covering all 11 JSX components (2,249 combined lines), behavioral SDK (204 lines), API layer (57 lines), CSS (120 lines), and Tailwind config (81 lines).*
