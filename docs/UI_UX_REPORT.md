# SentinelAI — Frontend UI/UX Report

> Generated from source code analysis. Covers all 10 JSX components, CSS, Tailwind config, behavioral SDK, and API layer.

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
| Styling | Tailwind CSS 3.4 (no custom theme extensions, no custom CSS beyond base body) |
| Icons | lucide-react v0.364 |
| Charts | recharts v2.12 |
| HTTP | axios v1.6.8 |
| No TypeScript | All JSX files are plain JavaScript |
| Port | Dev server on `:3000` |
| API Base | `VITE_API_BASE_URL` env var, default `http://localhost:9000/api` |

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

**ProtectedRoute** wraps children; if `getAuthToken()` returns falsy, redirects to `/login`. No token refresh or silent re-auth is implemented.

**AdminGuard** checks token + JWT `is_admin` claim. Shows a centered spinner during check, redirects to `/login?error=unauthorized` if not admin.

---

## 3. Global Theme & Layout Shell

### 3.1 Tailwind Configuration (`tailwind.config.js`)
- **No custom theme extensions.** All colors, spacing, typography, breakpoints are Tailwind defaults.
- Scan paths: `./index.html`, `./src/**/*.{js,ts,jsx,tsx}`
- No plugins, no `darkMode` config (uses class-based `dark` — not applied anywhere because the app is always-dark via `bg-gray-900` body class).

### 3.2 Base CSS (`index.css`)
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-900 text-white font-sans antialiased;
  }
}
```
- Background: `bg-gray-900` (#111827)
- Text: `text-white` (#ffffff)
- Font: `font-sans` (Tailwind default sans stack)
- Rendering: `antialiased`
- No global resets beyond Tailwind's preflight.

### 3.3 Entry Point (`index.html`)
```html
<body class="bg-gray-900 text-white">
  <div id="root"></div>
</body>
```
Title tag: **"SentinelAI Dashboard"**

---

## 4. Login Page (`/login`)

**File:** `Login.jsx` (286 lines)

### 4.1 Page Layout
- `min-h-screen` viewport coverage
- Flexbox centering: `flex flex-col justify-center items-center p-4`
- Relative positioning with `overflow-hidden` for background effects

### 4.2 Background Design
Two large blurred gradient orbs positioned absolutely:
- **Top-left orb:** `top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-500/20 blur-[120px] rounded-full`
- **Bottom-right orb:** `bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-500/20 blur-[120px] rounded-full`

These create a subtle purple-blue atmospheric glow effect behind the form card.

### 4.3 Login Card
- **Dimensions:** `w-full max-w-md` (max 448px width)
- **Background:** `bg-gray-800/50` (semi-transparent dark slate) with `backdrop-blur-xl` (glassmorphism)
- **Border:** `border border-gray-700` (#374151) — subtle 1px border
- **Padding:** `p-8` (32px all sides)
- **Border radius:** `rounded-2xl` (16px)
- **Shadow:** `shadow-2xl`
- **Z-index:** `z-10` (above background orbs)

### 4.4 Logo / Icon Area (centered above form)
```
Shield icon container:
  bg-blue-500/20            → 20% opacity blue backdrop
  p-3                       → 12px padding
  rounded-full              → fully circular
  ring-1 ring-blue-500/50   → thin blue border ring

Shield icon (lucide-react):
  w-8 h-8                   → 32x32px
  text-blue-400             → #60a5fa
```

**Title:** "SentinelAI" — `text-3xl font-bold tracking-tight`
**Subtitle:** "Behavioral Intelligence Platform" — `text-gray-400 text-sm text-center`

### 4.5 Form Fields

**Email field:**
- Label: "Email Address" — `text-sm font-medium text-gray-300`
- Input background: `bg-gray-900/50` with `border border-gray-700`
- Text color: `text-white`
- Border radius: `rounded-lg` (8px)
- Padding: `pl-10 pr-4 py-2.5` (left pad for icon, right pad, 10px vertical)
- Focus state: `focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500`
- Transition: `transition-all`
- Placeholder: `admin@sentinelai.com` — gray by default
- Icon: `Mail` (lucide) — `h-5 w-5 text-gray-500`, absolute positioned left with `pl-3`

**Password field:**
- Label: "Password" — `text-sm font-medium text-gray-300`
- Same styling as email but with `Lock` icon
- Placeholder: `••••••••`
- Type: `password` (obscured)

### 4.6 Submit Button (Login)
```
Background:   bg-gradient-to-r from-blue-600 to-indigo-600
              hover:from-blue-500 hover:to-indigo-500
Text:         text-white font-semibold
Padding:      py-2.5 px-4
Width:        w-full
Radius:       rounded-lg (8px)
Layout:       flex items-center justify-center space-x-2
Transforms:   hover:scale-[1.02] active:scale-[0.98]
Focus:        focus:ring-2 focus:ring-blue-500/50
Disabled:     disabled:opacity-70 disabled:cursor-not-allowed
Transition:   transition-all
```

**Button content when idle:** `Secure Login` text + `ArrowRight` icon (w-4 h-4)
**Button content when loading:** Spinning loader — `w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin`

### 4.7 Navigation Links
- **"Forgot Password?"** link below button: `text-sm text-gray-400 hover:text-blue-400 transition-colors`. Links to `/forgot-password`.
- **"New to SentinelAI? Register Account"** at card bottom: `text-sm text-gray-400` with `text-blue-400 hover:text-blue-300 font-medium` link to `/register`.

### 4.8 OTP Verification Sub-form (shown when `otp_required`)
Replaces the login form entirely:
- **OTP Code input:** `tracking-[0.3em] text-center`, placeholder `123456`, `maxLength={6}`, `inputMode="numeric"`
- **Verify OTP button:** Green gradient — `from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-emerald-500` with same hover/active transforms

### 4.9 CAPTCHA Verification Sub-form (shown when `captcha_required`)
Replaces the login form entirely:
- **CAPTCHA prompt display:** `rounded-lg border border-gray-700 bg-gray-900/50 px-4 py-3 text-center tracking-[0.4em] text-lg font-semibold text-blue-300`
- **Answer input:** `tracking-[0.3em] text-center uppercase`, placeholder `ABC123`
- **Verify CAPTCHA button:** Amber/orange gradient — `from-amber-600 to-orange-600`

### 4.10 Alert / Info Banners
- **Error banner:** `rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200`
- **Info banner:** `rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm text-blue-200`
- Both positioned above the form, below the title area.

### 4.11 Behavioral SDK Indicator
Below the card, centered:
```
Live dot indicator:
  w-2 h-2 rounded-full bg-green-500
  with animate-ping wrapper (w-2 h-2 bg-green-400)
Text: "Behavioral SDK Active" — text-xs text-gray-500
```

### 4.12 Form Submission & `is_blocked` Handling
The login handler (`handleLogin`) sends `POST /login` with:
- `email`, `password`, `behavioralData`, `ip_address: '127.0.0.1'`, `user_agent: navigator.userAgent`, `country: 'US'`

Response handling order:
1. `otp_required` → OTP sub-form, auto-sends `POST /otp/send` with session ID
2. `captcha_required` → CAPTCHA sub-form with `captcha_token` and `captcha_prompt`
3. `is_blocked` → Shows `response.data.message` as error (handles both quarantined and hard-blocked)
4. `token` present → Stores session, navigates admin to `/dashboard`, non-admin to `/events`

---

## 5. Register Page (`/register`)

**File:** `Register.jsx` (151 lines)

### 5.1 Layout & Background
Same structural pattern as Login:
- `min-h-screen bg-gray-900 flex flex-col justify-center items-center p-4 relative overflow-hidden`
- Background orbs: `bg-indigo-500/20` (top-right) + `bg-teal-500/20` (bottom-left)
- Card: same `max-w-md bg-gray-800/50 backdrop-blur-xl border border-gray-700 p-8 rounded-2xl shadow-2xl`

### 5.2 Visual Identity
- **Icon container:** `bg-indigo-500/20 p-3 rounded-full ring-1 ring-indigo-500/50`
- **Icon:** `ShieldAlert` — `w-8 h-8 text-indigo-400`
- **Title:** "Create Account" — `text-3xl font-bold tracking-tight`
- **Subtitle:** "Behavioral analysis will run during signup" — `text-gray-400 text-sm text-center`

### 5.3 Form Fields (3 fields + submit)

**Full Name:** `User` icon, placeholder `John Doe`
**Email Address:** `Mail` icon, placeholder `john@example.com`
**Password:** `Lock` icon, placeholder `••••••••`

All inputs share Login's styling pattern: `bg-gray-900/50 border-gray-700 rounded-lg` with indigo focus rings (`focus:ring-indigo-500/50 focus:border-indigo-500`).

### 5.4 Submit Button
```
Gradient: from-indigo-600 to-purple-600
Hover:    from-indigo-500 to-purple-500
Extra:    mt-2
```

**Text:** `Complete Registration` + `ArrowRight`

### 5.5 Success & Error Handling
- **Error:** Red banner (same as Login's error banner)
- **Success:** Emerald banner — `rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-200` showing trust score. Auto-redirects to `/login` after 1200ms.

### 5.6 Navigation
`"Already have an account? Sign In"` — indigo link to `/login`.

---

## 6. Forgot Password Page (`/forgot-password`)

**File:** `ForgotPassword.jsx` (110 lines)

### 6.1 Layout
Same dual-orb background (blue/purple), same glass card, same logo area (blue `Shield` icon, "SentinelAI" title).
Subtitle: "Reset your password"

### 6.2 Form
Single field: Email with `Mail` icon, placeholder `you@example.com`

Button: "Send Reset Link" — same blue-to-indigo gradient. No ArrowRight icon.

Footer: "Back to Login" with `ArrowLeft` icon, blue link.

### 6.3 Post-submit State
Replaces form with success view:
- **CheckCircle icon:** `w-16 h-16 bg-emerald-500/20 rounded-full ring-1 ring-emerald-500/50` containing `w-8 h-8 text-emerald-400`
- **Text:** "Check your email" — `text-emerald-300 font-medium`
- **Detail:** "If that email is registered, we've sent a password reset link. It expires in 15 minutes." — `text-gray-400 text-sm`
- **Link:** "Back to Login" with `ArrowLeft`

---

## 7. Reset Password Page (`/reset-password`)

**File:** `ResetPassword.jsx` (152 lines)

### 7.1 Token Validation
Reads `token` from `?token=` search param. If no token:
- Centered error card: "Invalid reset link. No token provided." — `text-red-400`
- Link to request new link with `ArrowLeft`

### 7.2 Layout (with valid token)
Same dual-orb background, same glass card, same logo area.
Subtitle: "Choose a new password"

### 7.3 Form Fields

**New Password:**
- `Lock` icon, placeholder "New password", `minLength={8}`
- Same styling as Login password

**Confirm Password:**
- `Lock` icon, placeholder "Confirm new password", `minLength={8}`
- Same styling

### 7.4 Submit & Validation
Client-side checks before API call:
1. Passwords must match ("Passwords do not match.")
2. Password length >= 8 ("Password must be at least 8 characters.")

Button: "Reset Password" — blue-to-indigo gradient.

### 7.5 Post-submit State
- CheckCircle icon (same pattern as ForgotPassword)
- Text: "Password reset successful" — `text-emerald-300`
- Detail: "You can now log in with your new password."
- Button: "Go to Login" — full-width blue gradient, navigates to `/login`

---

## 8. Events Page (`/events`)

**File:** `Events.jsx` (23 lines)

### 8.1 Current State
**Placeholder** — "Event Platform — under construction" — `text-lg text-gray-400`, centered.
Single "Logout" button: `px-6 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg border border-gray-700 transition-colors`

### 8.2 Intended Use
This is the landing page for non-admin authenticated users (students/attendees). It is intended to show event-related interfaces but has not been implemented yet.

---

## 9. Dashboard — Command Center (`/dashboard`)

**File:** `Dashboard.jsx` (434 lines)

This is the primary admin interface — a comprehensive monitoring dashboard with 5 panels, real-time polling, and user management.

### 9.0 Polling
- Initial load on mount + auto-refresh every **4 seconds** via `setInterval`
- 5 parallel API calls: `/analytics/summary`, `/analytics/velocity?window=1h&bucket=1min`, `/analytics/trust-distribution`, `/users?limit=10&offset=N`, `/alerts?limit=15`
- Auto-logout on 401 response
- Caches `mounted` flag to prevent state updates after unmount

### 9.1 Header
- **Left:** `Shield` icon (blue) in `bg-blue-500/20 p-2 rounded-lg ring-1 ring-blue-500/50` container
- **Title:** "SentinelAI Command Center" — `text-2xl font-bold tracking-tight`
- **Subtitle:** "Behavioral Intelligence Platform" — `text-sm text-gray-400`
- **Right side (header actions):**
  - **System Active badge:** `text-green-400 bg-green-400/10 px-3 py-1.5 rounded-full border border-green-400/20` with `Server` icon (w-4 h-4)
  - **Logout button:** `flex items-center space-x-2 text-gray-300 hover:text-white bg-gray-800/80 border border-gray-700 px-3 py-1.5 rounded-full` with `LogOut` icon (w-4 h-4)

### 9.2 KPI Cards Row
**Grid:** `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8`
**Cards:** 4 cards in a responsive row

Each `KPICard` component:
- **Container:** `bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm hover:border-gray-600 transition-colors`
- **Inner layout:** `flex justify-between items-start`
- **Value:** `text-3xl font-bold text-white`
- **Label:** `text-sm font-medium text-gray-400 mb-1`
- **Icon container:** `bg-{color}/10 p-3 rounded-lg border border-gray-700/50`
- **Icon:** `w-6 h-6 text-{color}`

The 4 KPIs:

| # | Title | Icon | Color | Background |
|---|-------|------|-------|------------|
| 1 | Total Users | `Users` | `text-blue-400` | `bg-blue-400/10` |
| 2 | Flagged Today | `AlertTriangle` | `text-yellow-400` | `bg-yellow-400/10` |
| 3 | Bot Waves Detected | `Activity` | `text-red-400` | `bg-red-400/10` |
| 4 | Quarantined | `Lock` | `text-orange-400` | `bg-orange-400/10` |

Each card also optionally supports a `trend` prop (red text with `Activity` icon and arrow + "vs last hour"), but the dashboard currently passes no trend data.

### 9.3 Panel Layout (Charts Row)

**Grid:** `grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8`

Two panels in this row:

#### Panel A: Registration Velocity Chart (spans 2/3)
- **Container:** `lg:col-span-2 bg-gray-800/50 border border-gray-700 rounded-xl p-6 shadow-lg backdrop-blur-sm`
- **Height:** `h-[22rem]` (352px) default, `lg:h-[26rem]` (416px) on desktop
- **Layout:** `flex flex-col` — chart fills remaining space via `flex-1 min-h-0`
- **Title:** `text-lg font-semibold` with `Activity` icon (blue-400)

**Chart: Recharts LineChart**
- `ResponsiveContainer` width=100% height=100% (fills parent flex-1)
- Data mapped from `/analytics/velocity`: `time` (HH:MM formatted timestamp) vs `signups` (registrations count)
- XAxis: `dataKey="time"`, stroke `#9ca3af`, no axis line, no tick line, `tickMargin={12}`, `height={32}`
- YAxis: stroke `#9ca3af`, no axis line, no tick line
- CartesianGrid: `strokeDasharray="3 3"`, stroke `#374151`, no vertical lines
- Tooltip: dark theme — bg `#1f2937`, border `#374151`, `borderRadius="0.5rem"`, text `#60a5fa`
- Line: `type="monotone"`, `stroke="#3b82f6"` (blue-500), `strokeWidth={3}`
- Dots: `r={4}`, fill `#3b82f6`, `strokeWidth={2}`, stroke `#1e3a8a`
- Active dot: `r={6}`, fill `#60a5fa`, no stroke
- Margins: `{ top: 6, right: 8, left: 0, bottom: 16 }`

#### Panel B: Live Threat Feed (spans 1/3)
- **Container:** Same styling, same heights
- **Title:** `text-lg font-semibold` with `ShieldAlert` icon (red-400)
- **Scroll:** `overflow-y-auto pr-2 space-y-4` — vertical scrolling feed

**Alert cards** — each one:
- Container: `bg-gray-900/50 border border-gray-700 p-4 rounded-lg`
- Animation: `animate-in fade-in slide-in-from-right-4 duration-500`
- Severity badge (uppercase, bold, tracking-wider, px-2 py-0.5 rounded):
  - `high`: `bg-red-500/20 text-red-400 border border-red-500/30`
  - `medium`: `bg-orange-500/20 text-orange-400 border border-orange-500/30`
  - default: `bg-yellow-500/20 text-yellow-400 border border-yellow-500/30`
- Alert type label (appears twice — once in badge, once in description)
- Timestamp: `text-xs text-gray-500`
- Description: `text-sm text-gray-300 mt-2`
- Emoji icons by alert type:
  - `bot_wave`, `velocity_spike` → 🤖
  - `geo_drift` → 🌍
  - `speed_bot` → ⚡
  - `duplicate_device` → 📱
  - `email_pattern` → ✉️
  - default → ⚠️

### 9.4 Panel Layout (Bottom Row)

**Grid:** `grid grid-cols-1 lg:grid-cols-3 gap-6`

#### Panel C: Trust Score Distribution (spans 1/3)
- **Container:** same styling, same `h-[22rem]`/`h-[26rem]` height
- **Title:** "Trust Score Distribution" — `text-lg font-semibold mb-6`
- **Chart overflow:** `flex-1 min-h-0`

**Chart: Recharts BarChart (horizontal)**
- `layout="vertical"`
- Margins: `{ top: 0, right: 30, left: 20, bottom: 0 }`
- XAxis: type `number`, stroke `#9ca3af`, no axis line, no tick line
- YAxis: dataKey `range`, type `category`, stroke `#9ca3af`, no axis line, no tick line
- CartesianGrid: `strokeDasharray="3 3"`, stroke `#374151`, no horizontal lines
- Tooltip: same dark style, `cursor={{fill: '#374151', opacity: 0.4}}`
- Bars: `dataKey="count"`, `radius={[0, 4, 4, 0]}` (rounded right ends)
- Each bar `Cell` filled dynamically based on trust band:
  - `green` (#22c55e) — Safe (70+)
  - `yellow` (#eab308) — Suspicious (40-69)
  - `orange` (#f97316) — Quarantine (20-39)
  - `red` (#ef4444) — Blocked (<20)
  - `darkred` (#7f1d1d) — highest risk

#### Panel D: User Forensics Table (spans 2/3)
- **Container:** same styling, same height, `overflow-hidden flex flex-col`

**Header:**
- Title: "User Forensics" — `text-lg font-semibold`
- Search input: `bg-gray-900 border border-gray-700 text-sm rounded-lg pl-9 pr-3 py-1.5 focus:outline-none focus:border-blue-500 transition-colors` with `Search` icon (w-4 h-4 text-gray-500) placeholder "Search users or IPs..."

**Table:**
- `w-full text-left text-sm`
- Thead: `text-xs text-gray-400 uppercase bg-gray-900/50 border-y border-gray-700`
- 5 columns: User | IP Address | Trust Score | Status | Action (right-aligned)
- Cell padding: `px-4 py-3`
- Body: `divide-y divide-gray-800`
- Rows: `hover:bg-gray-800/80 transition-colors group`

**Column "User":** `font-medium text-gray-200` for email, `text-xs text-gray-500` for registration date

**Column "IP Address":** `text-gray-400 font-mono text-xs`, shows `n/a` if no IP

**Column "Trust Score":** Two elements:
- Progress bar: `w-full bg-gray-700 rounded-full h-1.5 max-w-[4rem]` (64px) with inner colored bar
- Bar color based on score: `<20` = `bg-red-500`, `<40` = `bg-orange-500`, `<70` = `bg-yellow-500`, else `bg-green-500`
- Bar width set as `style={{ width: \`${user.trust_score}%\` }}`
- Score value: `text-xs font-bold text-gray-300`

**Column "Status":** Colored badge:
- `blocked`: `bg-red-500/10 text-red-400 border-red-500/20`
- `quarantined`: `bg-orange-500/10 text-orange-400 border-orange-500/20`
- default (active/safe): `bg-green-500/10 text-green-400 border-green-500/20`

**Column "Action":** `ChevronRight` icon button (w-4 h-4) — `text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 p-1.5 rounded-md border border-gray-700`
- Navigates to `/dashboard/users/${user.user_id}/timeline`

**Empty state:** "No users match your search." — `text-sm text-gray-400 text-center`, `colSpan={5}`

**Pagination Controls (below table):**
Wrapper: `mt-6 flex items-center justify-between pt-4 border-t border-gray-700`
- **Left:** "Showing X – Y of Z users" — `text-xs text-gray-400`
- **Right:** Page buttons with:
  - `← Prev` / `Next →` buttons: `px-3 py-1.5 text-xs font-medium rounded-md border border-gray-700 bg-gray-900/50 text-gray-300 disabled:opacity-50`
  - Page number buttons: current page = `bg-blue-500/20 border-blue-500/50 text-blue-400`, others = `border-gray-700 bg-gray-900/50 text-gray-300 hover:bg-gray-800`
  - Ellipsis (`...`) for skipped ranges — `text-gray-500`
  - Logic: shows only current page, ±1 neighbor, first, and last page; others collapsed into `...`

---

## 10. User Timeline (`/dashboard/users/:userId/timeline`)

**File:** `UserTimeline.jsx` (418 lines)

### 10.1 Dual Mode
This component operates in two modes controlled by the `mode` prop:

**Modal mode (`mode="modal"`, default):**
- Overlay: `fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4`
- Panel: `max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col` — `bg-gray-900 border border-gray-700 rounded-xl shadow-2xl`
- Close button: `X` icon (w-6 h-6)

**Page mode (`mode="page"`):**
- Container: `min-h-screen bg-gray-900 text-white p-6`
- Panel: `mx-auto w-full max-w-6xl bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden`
- Shows breadcrumb nav: "Dashboard → User timeline"
- Shows "Back to dashboard" button with `ArrowLeft`
- Has filter bar below header
- Close button: `X` icon (w-5 h-5), gray text

### 10.2 Header (shared)
- Pre-header: "Forensic Replay" — `text-xs uppercase tracking-[0.2em]` with `History` icon (w-4 h-4)
- Title: "Activity Timeline" — `text-xl font-bold`
- Subtitle: user email — `text-sm text-gray-400`
- Right: Close button

### 10.3 Filter Bar (page mode only)
Appears below header: `border-b border-gray-700 bg-gray-800/40 p-6`

**Filter bar header:**
- Left: `Filter` icon (blue-400) + "Timeline filters"
- Right: "X of Y events shown" counter + **Export CSV button**

**Export CSV button:**
```
rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-1.5 text-blue-300
hover:bg-blue-500/20
disabled:opacity-40 disabled:cursor-not-allowed
```
Generates CSV with columns: timestamp, action, description, trust_score, country, ip_address, user_agent, metadata. Triggers browser download.

**3 dropdown filters** (responsive: `grid gap-4 md:grid-cols-3`):

**Filter 1 — Action Type:**
- Label: `SlidersHorizontal` icon + "Action type"
- Select options: All actions, Register, Login, OTP sent, OTP verified, Flagged, Quarantined

**Filter 2 — Time Window:**
- Label: `CalendarRange` icon + "Time window"
- Select options: All time, Last 24 hours, Last 7 days, Last 30 days

**Filter 3 — Trust Band:**
- Label: `Filter` icon + "Trust band"
- Select options: All trust bands, High risk (<20), Medium risk (20-39), Low risk (40-69), Safe (70+)

**Reset Filters button:** `text-xs text-gray-400 hover:text-white`, right-aligned below filters.

### 10.4 Filter Logic (client-side)
1. **Action filter:** Matches `event.action_type || event.action` lowercase against selected value
2. **Trust band filter:** Maps score to band (`<20`→high, `20-39`→medium, `40-69`→low, `70+`→safe)
3. **Time window filter:** Computes cutoff timestamp from now (24h / 7d / 30d) and filters by `event.timestamp`

### 10.5 Event Cards
Each event card in the timeline:
- **Container:** `bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors`
- **Top row:** Action badge + optional trust score + optional country badge
  - Action badge: `text-xs font-bold uppercase tracking-wider px-2 py-1 rounded border` with color based on action type:
    - `register`/`registration`: `bg-blue-500/20 text-blue-400 border-blue-500/30`
    - `login`: `bg-green-500/20 text-green-400 border-green-500/30`
    - `otp_sent`/`otp_verified`: `bg-cyan-500/20 text-cyan-400 border-cyan-500/30`
    - `event_signup`: `bg-purple-500/20 text-purple-400 border-purple-500/30`
    - `flagged`: `bg-red-500/20 text-red-400 border-red-500/30`
    - `quarantined`: `bg-orange-500/20 text-orange-400 border-orange-500/30`
    - default: `bg-gray-500/20 text-gray-400 border-gray-500/30`
  - Trust score: `text-xs font-bold`, color by band (<20 red, <40 orange, <70 yellow, 70+ green)
  - Country: `text-xs font-medium px-2 py-1 rounded border border-gray-600 text-gray-300`
- **Description:** `text-sm text-gray-300 mb-3`
- **Metadata grid** (2-column responsive): `grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-gray-400`
  - **Timestamp:** `Clock` icon + `new Date(event.timestamp).toLocaleString()`
  - **IP Address:** `MapPin` icon + monospace IP (if present)
  - **User Agent:** `Zap` icon + truncated UA text (if present, spans 2 cols)
  - **Metadata JSON:** `md:col-span-2 bg-gray-900/70 border border-gray-700 rounded-md p-3` with `BadgeAlert` icon + "Metadata" header + `<pre>` formatted JSON in `text-[11px] leading-5 text-gray-400`

### 10.6 Empty / Loading / Error States
- **Loading:** Centered `Loader` icon (w-8 h-8, text-blue-400, animate-spin) in `h-64` container
- **Error:** Red banner with `AlertCircle` icon — `bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400`
- **Empty results:** `text-center py-12 text-gray-400` — `Clock` icon (w-12 h-12, opacity-50) + "No activity matches the current filters"

---

## 11. Behavioral Fingerprinting SDK

**File:** `behavioral.js` (204 lines)

### 11.1 Tracking Architecture
- Activated via `startTracking()` on component mount
- Deactivated via `stopTracking()` on unmount
- `useBehavioral()` React hook auto-calls `startTracking()` if `window` is defined and returns `getPayload`
- All signals collected client-side, sent as opaque payload with form submissions

### 11.2 Signals Collected

| Signal | Description | Collection Method |
|--------|-------------|-------------------|
| `typing_variance_ms` | Standard deviation of inter-keypress intervals (ms) | `keydown` listener → timestamps array → compute stddev |
| `time_to_complete_sec` | Total time from start to submission (seconds) | Delta between `startTracking` and `getPayload` call |
| `session_tempo_sec` | Mean interval between all interactions (seconds) | Combined key/mouse/focus timestamps → average interval |
| `mouse_entropy_score` | Directional entropy of mouse movements (0-1) | Throttled mousemove → direction bucketing (up/down/left/right) → Shannon entropy |
| `fill_order_score` | Naturalness of form field focus order (0-1) | `focusin` listener → field sequence → uniqueness / repetition ratio |
| `mouse_move_count` | Throttled mouse move count | Throttled at 100ms intervals |
| `keypress_count` | Raw keypress count | Every keydown event |

### 11.3 Demo Override
`window.__DEMO_OVERRIDE__` — if set in browser console, `getPayload()` returns the override object directly, bypassing all tracking. Intended for presentations.

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
- `isAdmin()` — decodes JWT payload (base64 `atob` split on `.`), checks `payload.is_admin === true`
- No token refresh or expiry checking

---

## 13. Error & Loading States (Cross-Cutting)

### 13.1 Error Banners (consistent pattern across all auth forms)
```
rounded-lg border border-{color}-500/30 bg-{color}-500/10 px-4 py-3 text-sm text-{color}-200
```
- Red (`red-`): Errors
- Blue (`blue-`): Info messages (login OTP/captcha prompted)
- Emerald (`emerald-`): Success messages

### 13.2 Loading Spinner (consistent pattern across all buttons)
```
w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin
```
Replaces button text when `isLoading` is true.

### 13.3 Dashboard Loading
No explicit skeleton or shimmer — all data state shows `'...'` placeholder in KPI values during load. Charts render empty until data arrives.

### 13.4 AdminGuard Loading
`min-h-screen bg-gray-900 flex items-center justify-center` with a spinning `w-6 h-6` blue spinner.

---

## 14. Responsive Behavior Summary

All responsive breakpoints use Tailwind defaults:
- **`md:` breakpoint** (768px): KPI cards `md:grid-cols-2`, table pagination
- **`lg:` breakpoint** (1024px): KPI cards `lg:grid-cols-4`, charts/panels `lg:grid-cols-3`, panel heights `lg:h-[26rem]` vs `h-[22rem]`,
  Timeline filter bar `md:grid-cols-3`, event metadata `md:grid-cols-2`

**Mobile layout (below md):**
- All charts and tables stack vertically (single column)
- Page padding: `p-6` on desktop, no change for mobile (consistent `p-6` on dashboard, `p-4` on auth pages)
- Tables horizontally scrollable (`overflow-x-auto`)
- Timeline applies `max-h-[90vh]` modal approach for smaller containers

**Auth pages (all of them):**
- Always centered single-column (max-w-md = 448px max)
- Sacrifice horizontal space for focus on the form

---

## Appendix A: Color Palette Summary

All colors are raw Tailwind defaults — no custom tokens.

| Token | Hex | Usage |
|-------|-----|-------|
| `gray-900` | #111827 | Page backgrounds, table header bg, input bg |
| `gray-800` | #1f2937 | Card backgrounds (50% opacity), button bg |
| `gray-700` | #374151 | Borders, grid lines |
| `gray-400` | #9ca3af | Secondary text, axis labels, icon fills |
| `gray-300` | #d1d5db | Primary body text, labels |
| `gray-500` | #6b7280 | Tertiary text, muted icons |
| `white` | #ffffff | Headings, primary text |
| `blue-400` | #60a5fa | Secondary accent (icons, links) |
| `blue-500` | #3b82f6 | Primary chart line, focus rings |
| `blue-600` | #2563eb | Gradient start (buttons) |
| `indigo-400` | #818cf8 | Register accent |
| `indigo-600` | #4f46e5 | Register gradient start |
| `purple-500` | #a855f7 | Background orb, register gradient end |
| `emerald-600` | #059669 | OTP verify gradient start |
| `amber-600` | #d97706 | Captcha verify gradient start |
| `green-400/500` | #4ade80 / #22c55e | Safe/active status, SDK indicator |
| `yellow-400` | #facc15 | Suspicious band (#eab308 in bands) |
| `orange-400/500` | #fb923c / #f97316 | Quarantine band |
| `red-400/500` | #f87171 / #ef4444 | Blocked band, error states |
| `cyan-400` | #22d3ee | OTP badge in timeline |
| `black/50` | rgba(0,0,0,0.5) | Modal overlay |

## Appendix B: Chart and Graph Details

| Chart | Type | Library | Data Source | Refresh |
|-------|------|---------|-------------|---------|
| Registration Velocity | Line (monotone) | recharts LineChart | `GET /analytics/velocity?window=1h&bucket=1min` | Every 4s |
| Trust Distribution | Horizontal Bar | recharts BarChart | `GET /analytics/trust-distribution` | Every 4s |

## Appendix C: Typography Scale

| Element | Class | Size (rem) | Weight |
|---------|-------|------------|--------|
| Dashboard title | `text-2xl font-bold` | 1.5rem (24px) | 700 |
| Auth page titles | `text-3xl font-bold` | 1.875rem (30px) | 700 |
| Panel titles | `text-lg font-semibold` | 1.125rem (18px) | 600 |
| KPIs (value) | `text-3xl font-bold` | 1.875rem (30px) | 700 |
| KPIs (label) | `text-sm font-medium` | 0.875rem (14px) | 500 |
| Table header | `text-xs uppercase` | 0.75rem (12px) | 400 |
| Table cells | `text-sm` | 0.875rem (14px) | 400 |
| Form labels | `text-sm font-medium` | 0.875rem (14px) | 500 |
| Submit buttons | `font-semibold` | default (~16px) | 600 |
| Timeline action badges | `text-xs font-bold uppercase` | 0.75rem (12px) | 700 |
| Small meta | `text-xs` | 0.75rem (12px) | 400 |
| Timeline metadata JSON | `text-[11px]` | 0.6875rem (11px) | 400 |
| Subtle hints | `text-[11px] uppercase tracking-wider` | 0.6875rem (11px) | 400 |

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
          <Dashboard>
            <KPICard /> x4
            <LineChart>        ← recharts
            <BarChart>         ← recharts
            <table> + pagination
          </Dashboard>
        </AdminGuard>
        <AdminGuard>
          <UserTimeline>
            [filter bar]
            [event cards]
          </UserTimeline>
        </AdminGuard>
      </ProtectedRoute>
    </Routes>
  </BrowserRouter>
</App>
```

---

*Report generated from source analysis on 2026-06-17.*
*Covering all 10 JSX components, behavioral SDK (204 lines), and API layer (57 lines).*
