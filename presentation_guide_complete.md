# CIPHER SENTINELS
# SentinelAI — Complete Presentation & Demo Guide

**Hackathon 360° 4.0 — Domain 5: Cyber Security & Forensic Science**
**KIIT University — Team Cipher Sentinels**

---

> **Quick Reference**
> - Total presentation time: 12 minutes + 3 minutes Q&A
> - Arindam: Hook + Slides 1–4 + Conclusion + Q&A lead
> - Atul: Architecture + Stack + Methodology (Slides 5–7) + Backend (Slides 8–9)
> - Akash: Security engine + ML + Results + Differentiators (Slides 8–11)
> - Debarshi: Frontend + Dashboard + Screenshots (Slides 13–14)
> - Parthiv: Testing + Metrics + Observability + Future scope
> - Demo accounts must be seeded BEFORE the presentation starts

---

## SECTION 1: Pre-Presentation Setup Checklist

Complete every step below at least 30 minutes before the presentation. Do not skip anything.

### 1.1 Start All Services

Use the Makefile from the repo root. Open four terminal windows and run:

**Terminal 1 — Backend Server:**
```
make start-backend
```
Wait until you see: `INFO: Application startup complete`

> **Note:** The Makefile reads `.env` from the repo root. Ensure your `.env` has `DATABASE_URL`, `JWT_SECRET`, `SMTP_EMAIL`, `SMTP_APP_PASSWORD`, and `FRONTEND_URL=http://localhost:3000` set (SMTP needed for OTP and password reset emails). Also verify `ADMIN_PASSWORD` is set to `Admin@2024` (or whatever password you use for the demo admin account).

**Terminal 2 — PostgreSQL + Monitoring Stack:**
```
make start-monitoring
```
Wait ~20 seconds, then verify: open http://localhost:9090 (Prometheus) and http://localhost:3001 (Grafana). Grafana login: admin / admin

**Terminal 3 — Frontend:**
```
make start-frontend
```
App opens at http://localhost:3000

**Terminal 4 — Attack Simulation (keep ready, do not run yet):**
Keep this window open. You will run `make attack-botwave` live during the demo.

### 1.2 Seed Demo Accounts

Run these in order ONCE before the presentation:

```
make seed-all
```

This runs both seeders: 50 normal users + 12 demo users across the full trust spectrum. The Makefile handles the virtual environment automatically.

| Email | Password | Trust | Status | Login Outcome | Role |
|---|---|---|---|---|---|
| `admin@sentinelai.dev` | `Admin@2024` | 100 | active | direct | admin |
| `admin.demo@sentinelai.local` | `DemoPass!234` | 98 | active | direct | admin |
| `ananya.sharma@sentinelai.local` | `DemoPass!234` | 91 | active | direct | user |
| `rahul.verma@sentinelai.local` | `DemoPass!234` | 86 | active | direct | user |
| `meera.patel@sentinelai.local` | `DemoPass!234` | 76 | active | direct | user |
| `ishaan.rao@sentinelai.local` | `DemoPass!234` | 68 | active | OTP | user |
| `pooja.ghosh@sentinelai.local` | `DemoPass!234` | 61 | active | OTP | user |
| `amit.bose@sentinelai.local` | `DemoPass!234` | 57 | active | OTP | user |
| `tanvi.khan@sentinelai.local` | `DemoPass!234` | 43 | active | OTP | user |
| `arjun.nair@sentinelai.local` | `DemoPass!234` | 31 | active | CAPTCHA | user |
| `rhea.das@sentinelai.local` | `DemoPass!234` | 15 | quarantined | Quarantine | user |
| `kabir.mehta@sentinelai.local` | `DemoPass!234` | 27 | quarantined | CAPTCHA | user |
| `divya.iyer@sentinelai.local` | `DemoPass!234` | 16 | blocked | blocked | user |
| `nikhil.joshi@sentinelai.local` | `DemoPass!234` | 8 | blocked | blocked | user |

> For a quick live demo showing all trust bands, run `python hackathon_demo.py` instead — it generates bot waves, credential stuffing, and geo-drift attacks with real-time dashboard output.

### 1.3 Verify Everything Works

| URL | What You Should See |
|-----|---------------------|
| http://localhost:3000 | SentinelAI login page |
| http://localhost:9000/docs | Swagger API docs |
| http://localhost:9090 | Prometheus targets page |
| http://localhost:3001 | Grafana overview dashboard |

### 1.4 Makefile Quick Reference

All common operations are available as `make` targets from the repo root:

| Command | What It Does |
|---------|-------------|
| `make install` | Install all deps (backend + frontend) |
| `make start-backend` | Start FastAPI on port 9000 |
| `make start-frontend` | Start Vite on port 3000 |
| `make start-monitoring` | Start Postgres + Prometheus + Grafana |
| `make stop-monitoring` | Stop monitoring stack |
| `make seed-all` | Seed 50 normal + 12 demo users |
| `make seed-demo` | Seed only the 12 demo dashboard users |
| `make test` | Run full offline test suite |
| `make test-rules` | Run rules engine unit tests (standalone, offline) |
| `make test-scorer` | Run trust score pipeline tests (standalone, offline) |
| `make attack-botwave` | Simulate 15 bot registrations |
| `make attack-geodrift` | Simulate cross-country geo drift |
| `make attack-all` | Run all 3 attack scenarios |
| `make simulate-load` | Load test: 50 users, 10 workers |
| `make simulate-comprehensive` | Run 6 security attack scenarios |
| `make simulate-hackathon` | Run parallel hackathon demo |
| `make train-model` | Retrain Isolation Forest model |
| `make model-predict` | Quick ML sanity check (offline) |
| `make status` | Print system status & detection coverage |
| `make mon-logs` | Tail monitoring stack logs |
| `make clean` | Remove Python cache files |

---

## SECTION 2: Slide-by-Slide Presentation Script

### ARINDAM — Opening Hook + Slides 1–3 + Conclusion
*Time: ~2.5 minutes including hook. You open and close the entire presentation.*

> **HOOK:** Before touching any slide, face the camera and say this:
> "Every team today will show you a login form with an OTP. We are going to show you how platforms like Google, Cloudflare, and Stripe actually detect threats — not by asking what you did, but by asking how you did it. That distinction is the entire foundation of SentinelAI." Pause 2 seconds. Then switch to Slide 1.

**Slide 1 — Team Details (20 seconds):**
"We are Cipher Sentinels from KIIT University. I am Arindam Tripathi, tech lead and your point of contact. Our team of five built SentinelAI — a fully working, production-tested Behavioral Intelligence Platform for campus event security."

**Slide 2 — Team Members (20 seconds):**
Point to each member visible on camera: "Debarshi built our frontend and admin dashboard. Parthiv handled testing, simulation, and documentation. Atul built our entire backend — API, authentication, database. Akash designed our security intelligence layer including the ML model."

**Slide 3 — Problem Statement (30 seconds):**
"We chose Domain 5. The problem ECLearnix faces is real — fake registrations, bot-driven account creation, unauthorized access. The ask was smart, simple, effective. We took it further. We built something that thinks the way real security systems think."

**Slide 4 — Solution Overview (30 seconds):**
"SentinelAI is not a single security check. It is a pipeline: behavioral signals are collected by an invisible JavaScript SDK, scored by a Rules Engine and ML Anomaly Scorer in parallel, and fused into a single trust score from 0 to 100. That score determines exactly how much friction each user experiences — from seamless login all the way to quarantine. Three independent layers, one unified decision."

**Slide 5 — Architecture Diagram (20 seconds):**
"Here is the full system architecture. The flow starts at the user's browser, where behavioral data is collected. It hits the FastAPI backend, which queries PostgreSQL for historical context, runs the scoring pipeline, and writes every decision back to the database. Prometheus scrapes metrics from the API layer. Grafana visualizes them. Docker Compose orchestrates everything."

**Slide 6 — Technology Stack (20 seconds):**
"Frontend: React + Vite + TailwindCSS + Recharts. Backend: FastAPI + SQLAlchemy + Pydantic. Database: PostgreSQL with SQLite fallback. ML: scikit-learn Isolation Forest. Monitoring: Prometheus + Grafana. Auth: JWT + bcrypt + OTP via SMTP, with a complete forgot/reset password flow. Containerization: Docker Compose for the monitoring stack. All Python 3.11+, Node 20+."

**Slide 7 — Methodology: The Trust Score Pipeline (30 seconds):**
"Our methodology has three layers. Layer 1 is Heuristic Rules — deterministic checks like velocity and email patterns, worth up to 60 penalty points. Layer 2 is Behavioral Analytics — typing rhythm and mouse movement from the SDK, worth up to 25 points. Layer 3 is ML Anomaly Detection — Isolation Forest on a 7-dimensional feature vector, worth up to 15 points. The sum is subtracted from 100. The result drives four outcomes: direct login (70+), OTP (40–69), CAPTCHA (20–39), or quarantine (under 20)."

---

### ATUL — Backend Architecture + Methodology Steps 1–3
*Time: ~2 minutes. Arindam hands off with: "Atul, walk us through the backend."*

**Slide 8 — Your Cards: Behavioral Collector (receiving), Trust Engine (receiving), PostgreSQL**
"The backend is FastAPI — async Python that gave us automatic Swagger documentation and fast response times. Every request passes through a pipeline I designed."

"The foundation is PostgreSQL. We migrated from SQLite to Postgres during development and stress-tested it: 50 concurrent workers, 500 simultaneous database tasks, pool size of 10 — zero connection failures."

"Authentication uses JWT tokens with a layered OTP system. Here is what makes it smart: OTP only fires when the trust score drops below 70. High-trust users get a completely seamless login. This is Progressive Authentication — friction proportional to risk."

"OTP is delivered via Gmail SMTP with App Passwords. Sessions expire in 5 minutes and are single-use, stored in their own database table."

**Slide 9 — Your Steps: Signal Transmission + Heuristic Evaluation**
"When a user submits a form, behavioral signals arrive at my registration endpoint as a hidden JSON payload alongside the credentials. My endpoint immediately extracts IP address, user agent, and behavioral data and passes them to the scoring pipeline."

"Before the ML model even runs, my endpoint queries the database for two things: how many registrations came from this IP in the last 60 minutes, and how many accounts share the same user agent today. Every single event — registration, login, OTP sent, quarantine triggered — is written to the events table with a full forensic record."

Hand off: "I will pass to Akash for the intelligence layer."

---

### AKASH — Security Engine + ML + Results
*Time: ~2.5 minutes. Most technically impressive section. Speak slowly and confidently.*

**Slide 8 — Your Cards: ML Anomaly Scorer + Adaptive Response Logic**
"I built two parallel systems: the Rules Engine and the ML Anomaly Scorer."

"The Rules Engine is deterministic and fast. On registration, it checks four conditions: Is this IP registering too many accounts? Is the email sequential or disposable? Did the form complete in under 3 seconds? Is the same device fingerprint appearing across multiple accounts? A fifth check — platform-wide registration velocity — fires alerts without penalizing individuals. On login, a sixth check detects geographic drift: did this account appear from a different country within 2 hours?"

"The ML layer uses Isolation Forest — unsupervised scikit-learn. I trained it on 200 synthetic benign user vectors. It does not need labeled malicious data. It learns the shape of human behavior and flags statistical deviations. The model outputs an anomaly score between -1 and 0, contributing up to 15 penalty points. We can verify the model in one command: `make model-predict` runs a sanity check — feeds a benign vector and a bot vector through the loaded model and confirms the bot scores higher."

"The final trust score formula: 100, minus rule penalties up to 60, minus behavioral penalties up to 25, minus ML penalties up to 15. Clamped at zero."

**Slide 9 — Your Steps: ML Inference + Score Fusing**
"The feature vector has seven dimensions: typing variance, form completion time, mouse move count, IP registration frequency, email pattern score, keypress count, and session action rate. For a real human, typing variance is 80 to 400 milliseconds — naturally inconsistent. For a bot: under 10 milliseconds, perfectly uniform. That single signal separates 80% of cases."

**Slide 10 — Results (your slide entirely, use real numbers):**
"Real numbers from our simulation. 60-registration bot wave: 19 accounts correctly quarantined, confirmed by Prometheus metric sentinelai_auth_registration_total with status quarantined equal to 19."

"Credential stuffing scenario: 192 failed login attempts, all correctly identified, zero legitimate users affected."

"Geo drift: same account logging in from India then Germany within 47 minutes triggered an immediate high-severity alert."

"Most importantly: zero false positives. Every one of our 50 legitimately seeded users maintained active status throughout all simulation runs."

**Slide 11 — Key Differentiators (20 seconds):**
"Invisible behavioral collection — the user never knows they are being profiled. Progressive authentication — friction only when risk demands it. Dual-layer detection — deterministic rules catch known patterns, unsupervised ML catches the unknown. Human-in-the-loop — every quarantine is reviewable by an admin. Production-observable — every decision emits a Prometheus metric and writes a forensic event."

Hand off: "Debarshi will show what all of this looks like from the admin perspective."

---

### DEBARSHI — Frontend + Dashboard + Screenshots
*Time: ~2.5 minutes. Most visual section. Point to specific elements on screen.*

**Slide 8 — Your Card: Forensic Admin Dashboard**
"Everything Akash described surfaces in real time on the admin dashboard I built in React with Vite and TailwindCSS, with Recharts for data visualization."

"The dashboard has five live panels. The KPI row at the top shows total users, flagged today, bot waves detected, and quarantined count. The Registration Velocity chart plots signups per minute — when a bot wave hits, you see the spike immediately. The Live Threat Feed polls our alerts API every 4 seconds. The Trust Score Distribution shows a histogram of all users by band. And User Forensics is a searchable table with drill-in timeline for every user."

"I also built the behavioral fingerprinting SDK — 50 lines of JavaScript running silently on auth pages. It measures form completion time, standard deviation of keypress intervals, and mouse movement count. The user never sees it. But it is what separates a 2-second bot submission from a 45-second human registration."

"The login page also has a Forgot Password? flow — enter your registered email, receive a secure link, and set a new password. Tokens expire in 15 minutes and are single-use with SHA-256 hashed storage to prevent replay."

**Slides 13–14 — Screenshot Walkthrough:**

Slide 13: "This is our live system after running the seed and simulation scripts. 347 total users, 1,095 flagged today, 253 bot waves detected, 47 quarantined. The Live Threat Feed on the right shows geo drift alerts firing. The Trust Score Distribution shows the majority in the safe band with a smaller cluster in quarantined and blocked — exactly what we expect after a bot wave."

Slide 14: "On the left is the Forensic Replay view — the activity timeline for a specific user. Every event: registration, login attempt, IP, country, trust score at that exact moment, and full metadata including which rules fired and what each penalty was. Admins can filter by action type, time window, and trust band, and export to CSV for offline investigation."

Hand off: "Parthiv will walk through our testing and observability stack."

---

### PARTHIV — Testing + Observability + Future Scope
*Time: ~2 minutes. You prove the project is production-ready, not just a prototype.*

**Slide 9 — Your Steps: DB Persistence + Observability Emission**
"After every security decision, two things happen. The event is persisted to PostgreSQL — user ID, action, IP, country, trust score, and a JSON metadata blob of exactly which rules fired. This enables forensic replay."

"Second, the backend emits Prometheus metrics. Every API call increments labeled counters: registrations by outcome, logins by outcome, alerts by type, API errors by endpoint. These are exposed on a /metrics endpoint scraped by Prometheus every 10 seconds."

**Testing Methodology — Modular, Automated, Repeatable:**
"Every component is independently testable. The rules engine runs standalone with `make test-rules`. The full trust score pipeline runs offline with `make test-scorer`. The entire integration suite runs with `make test` — zero external dependencies needed."

"For load testing we use `make simulate-load` — 50 concurrent virtual users, 10 workers, hitting the API under realistic conditions. For security validation we use `make simulate-comprehensive` — six attack scenarios back-to-back covering bot waves, credential stuffing, geo drift, speed bots, duplicate devices, and email pattern abuse."

**Metrics Slide — Real Prometheus Numbers:**
"After our full varied simulation: 8 bot wave alerts created. 192 failed login attempts tracked. 116 API errors from malformed bot requests on the register endpoint. 19 accounts correctly quarantined, 3 correctly active."

"Database after simulation: 347 users, 369 events, 1,100 alerts, 5 OTP sessions, password reset tokens tracked in their own table."

"Connection pool stress test: 50 concurrent workers, 500 simultaneous tasks, pool size 10 — 100% success rate. Zero dropped connections."

**Slide 15 — Grafana Screenshot:**
"This is our Grafana dashboard running via Docker Compose. Six live panels: API request rate, RPS by endpoint, error rate, latency at p95 and p99, login attempts by outcome, and security rules triggered by type. The Prometheus screenshot shows us querying total API requests in real time using PromQL. The entire monitoring stack spins up with one command: make start-monitoring."

**Slide 12 — Future Scope:**
"Two challenges we solved: synthetic data generation — solved through custom Python simulation scripts. Shared campus gateway IPs — solved through browser-level device fingerprinting so the velocity rule does not penalize innocent users on the same Wi-Fi."

"Future directions: mobile biometrics using gyroscope and accelerometer data, LSTM-based sequence models replacing Isolation Forest for temporal pattern tracking, and decentralized threat intelligence sharing across campus platforms — the Prometheus metrics pipeline for this already exists."

Hand off back to Arindam: "Back to Arindam for our conclusion."

---

### ARINDAM — Conclusion

**Slide 16 — Conclusion (30 seconds):**
"SentinelAI does not just block threats. It understands intent. By modeling how users behave rather than simply what they do, we have built a system that keeps event ecosystems secure for the real campus community while staying one step ahead of automated threats. Thank you."

---

## SECTION 3: Live Demo — Step-by-Step

This section tells you exactly what to show, what to type, and what to say for each demo scenario.

Recommended demo order: Admin Login → Normal User → Forgot Password Flow → OTP User → Quarantined User → Blocked User → Live Bot Registration → Attack Script → Dashboard Reaction → Forensic Timeline → Prometheus → Grafana

### 3.1 RBAC Demo — Showing the Access Control Separation

This demonstrates that regular users cannot access the admin dashboard.

**Step 1** — Open http://localhost:3000/login
Show the standard login page. Say: "There are two types of users in SentinelAI: regular platform users who register for events, and admin operators who monitor threats. They have completely separate flows."

**Step 2** — Log in as a regular user first
Use `ananya.sharma@sentinelai.local` / `DemoPass!234`. Say: "This is a normal student account with a trust score of 91. Watch what happens after login." After login, you land on /events, NOT the dashboard.

**Step 3** — Try to manually navigate to /dashboard
Type http://localhost:3000/dashboard in the browser. The AdminGuard component catches it and redirects to /login?error=unauthorized. Say: "The frontend route guard reads the JWT payload. This account has is_admin: false. Access denied, redirected immediately."

**Step 4** — Try hitting the API directly
Open browser developer tools > Network tab. Try fetching http://localhost:9000/api/alerts. You get a 403 Forbidden. Say: "Even if someone bypasses the frontend, the backend require_admin dependency on every admin route returns 403. Two independent layers of access control."

**Step 5** — Log out, then log in as admin
Use `admin@sentinelai.dev` / `Admin@2024`. After login, the RootRedirect component sends admins to /dashboard. Say: "Admin credentials issue a JWT with is_admin: true. The route guard passes. The dashboard loads. Same login form, completely different experience based on role."

> **SAY THIS:** "Admin accounts are never created through the public registration form. They are provisioned only through a seeding script or environment variable on first startup. A regular user has no path to escalate their own privileges."

### 3.2 Forgot / Reset Password Demo

This demonstrates the complete password recovery flow, including security measures against email enumeration.

**Step 1** — Show the login page, point to the Forgot Password? link
Say: "Users who forget their password can self-recover. No admin intervention required. Clicking the link takes them to a dedicated forgot password page."

**Step 2** — Click Forgot Password?, enter an email
Navigate to http://localhost:3000/forgot-password. Enter `ananya.sharma@sentinelai.local` and submit.
Say: "The system sends a secure, single-use reset link to the registered email. Note that we always return success — even if the email does not exist in our system. This prevents attackers from enumerating which accounts are registered."

**Step 3** — Check the server console for the reset link
Switch to Terminal 1 (backend). The log shows:
```
INFO: Reset email would be sent to: ananya.sharma@sentinelai.local
INFO: Reset link: http://localhost:3000/reset-password?token=<token>
```
Say: "In development mode without SMTP, the link is logged to the console. In production, it goes to the user's email. The token is a 32-byte cryptographically random string, SHA-256 hashed before storage — even a database breach cannot expose active tokens."

**Step 4** — Click the link, reset the password
Copy the reset link from the console. Open it in the browser. The Reset Password page shows a new password form. Enter a new password (e.g., `NewPass!456`) and confirm.
Say: "The token is validated server-side: it must exist, not be expired (15-minute window), and not have been used before. All three checks happen atomically in a single database query."

**Step 5** — Log in with the new password
Navigate back to login. Use `ananya.sharma@sentinelai.local` / `NewPass!456`. Login succeeds.
Say: "The password hash is updated in the database. Existing JWT sessions are not invalidated — the user's other active sessions continue to work, which is standard practice to avoid force-logging users off their devices."

> **SAY THIS:** "Forgot password and reset password each have their own rate limits — 3 requests per minute per IP for forgot, 5 per minute per IP for reset. Coupled with the no-enumeration response, brute-forcing the recovery flow is not feasible."

### 3.3 Trust Score Demo — Five Users, Four Outcomes

Keep the admin dashboard open in one tab. Open the login page in another tab. Switch between them to show alerts appearing after each login.

Pick any accounts from the table in Section 1.2 — one from each outcome band. Common choices:

> **DEMO USER 1 — Safe User (Trust 91, Direct Login)**
> `ananya.sharma@sentinelai.local` / `DemoPass!234`
> Expected: Login succeeds immediately, no OTP, no friction
> Say: "Trust score of 91. Above the 70-point threshold. The system recognizes this as a low-risk user and allows direct login. Zero friction for legitimate users."
> Show: JWT token issued, redirected to /events
> 
> **DEMO USER 2 — OTP User (Trust 61, OTP Triggered)**
> `pooja.ghosh@sentinelai.local` / `DemoPass!234`
> Expected: OTP screen appears, email is sent, enter code to complete login
> Say: "Trust score of 61. Between 40 and 69 — the suspicious band. The system does not block this user outright. It applies friction: OTP verification. Check your email."
> Show: Type in the OTP that arrives. Login completes. Say: "Progressive authentication. Security friction proportional to risk."
> 
> **DEMO USER 3 — CAPTCHA User (Trust 31, CAPTCHA Challenge)**
> `arjun.nair@sentinelai.local` / `DemoPass!234`
> Expected: CAPTCHA prompt appears with an alphanumeric code to type
> Say: "Trust score of 31. Between 20 and 39 — the CAPTCHA band. The system needs a bit more proof but is not locking the account yet. The captcha is our last friction layer before quarantine."
> Show: Type the code shown, submit. Login completes. Say: "A captcha is the shallowest friction — a human solves it in seconds, a bot gets blocked."
> 
> **DEMO USER 4 — Quarantined User (Trust 15, Login Blocked)**
> `rhea.das@sentinelai.local` / `DemoPass!234`
> Expected: Login blocked with 'Account under review. An admin will review your account status.'
> Say: "Trust score of 15. Below the quarantine threshold of 20. This account was flagged during our bot wave simulation. The user cannot log in, but they are not permanently banned. They are in quarantine — rate-limited, heavily logged, pending admin review."
> Before proceeding, check the admin dashboard: rhea.das should appear in the Quarantined section with an Approve button.
> Show: Switch to admin dashboard. Find this account in User Forensics. Show the Approve button.
> Say: "The admin can approve them back to active, or permanently block them. Human-in-the-loop verification. This is how we avoid false-positive hard bans."
> 
> **DEMO USER 5 — Blocked User (Trust 8, Hard Block)**
> `nikhil.joshi@sentinelai.local` / `DemoPass!234`
> Expected: Login blocked with 'Account suspended.' message
> Say: "Trust score of 8. This account has been reviewed by an admin and permanently blocked. No OTP, no review option, no unblock option. Hard block. The difference from quarantine is subtle but critical: quarantine has an Approve button for admin review. Blocked users do not."

### 3.4 Live Bot Registration Demo — Showing Detection in Real Time

This shows a bot attempting to register and being caught. Use the browser console trick.

**Step 1** — Open the Register page at http://localhost:3000/register
Open browser developer tools (F12). Go to the Console tab. Keep it visible alongside the form.

**Step 2** — Paste the behavioral override in the console
Paste this exactly:
```javascript
window.__DEMO_OVERRIDE__ = {
  typing_variance_ms: 3,
  time_to_complete_sec: 1.2,
  mouse_move_count: 0,
  keypress_count: 44
}
```

**Step 3** — Fill the form with bot-like details
Email: `user99@temp.com` | Password: anything
Say: "We use a disposable email domain, and we have overridden the behavioral payload to simulate a headless browser: zero mouse movement, 1.2 second completion, 3 millisecond typing variance."

**Step 4** — Submit and show the response
The system returns: quarantined, trust score around 20–35 depending on database state.
Say: "Email pattern rule: minus 20 for the disposable domain. Speed bot rule: minus 20 for 1.2-second completion. Behavioral penalty: minus 25 for zero mouse movement and uniform typing. If our ML model flags it too, that adds more. The scoring is cumulative — one signal triggers quarantine, multiple signals confirm it."

**Step 5** — Switch to admin dashboard
Show the new alert in the Live Threat Feed. Show the quarantined account in User Forensics.

### 3.5 Attack Script Demo — Bot Wave + Geo Drift (Live Terminal)

Switch to Terminal 4. This is the most visually dramatic part of the demo. Run while the admin dashboard is visible.

**Step 1** — Run the bot wave scenario
```
make attack-botwave
```
Say: "We are sending 15 registrations in 8 seconds from a single IP with sequential email addresses. Watch the dashboard."

**Step 2** — Point to the dashboard while it runs
The Live Threat Feed populates with bot_wave alerts. The velocity chart spikes. The quarantined count increases. Say: "The velocity rule fired. The email pattern rule fired. 15 accounts, all quarantined, in under 10 seconds."

**Step 3** — Run the geo drift scenario
```
make attack-geodrift
```
Say: "Same account, logging in from India, then from Germany, 47 minutes apart. Watch for the geo_drift alert."

**Step 4** — Point to the geo drift alert in the feed
Say: "The system detected that this is geographically impossible for a real user. High-severity alert created. Admin notified."

> **Tip:** `make attack-all` runs all three scenarios (botwave + geodrift + speedbot) back-to-back if you want a single command.

### 3.6 Forensic Timeline Demo

Show the deep forensic capability. Judges love this.

**Step 1** — Click on a quarantined user in User Forensics
Find the bot account or the manually registered bot account. Click the arrow.

**Step 2** — Walk through the timeline
Show each event row. Point to: the timestamp, the IP, the country, the trust score at that moment, and the metadata JSON. Say: "Every single action this account took is recorded. Registration: trust score started at 18, these rules fired, these penalties applied. We can see exactly why this account was flagged."

**Step 3** — Show the filter controls
Filter by action type or time window. Say: "Admins can filter by action type, time window, or trust band. They can also export the full timeline as CSV for offline forensic investigation."

**Step 4** — Click Approve on the quarantined user
Say: "If the admin determines this was a false positive, they approve the account. Status returns to active. This is the human-in-the-loop verification step that prevents permanent bans on borderline cases."

---

## SECTION 4: Prometheus & Grafana Demo

Open http://localhost:9090 for Prometheus and http://localhost:3001 for Grafana. Have both ready before this section.

### 4.1 Prometheus Queries to Run Live

Prometheus is at http://localhost:9090. Go to Graph tab. Paste these queries one at a time.

**Query 1 — Total Registrations by Status:**
```
sentinelai_auth_registration_total
```
Say: "This shows every registration attempt broken down by outcome: active, quarantined, and blocked. After our bot wave simulation, you can see 19 quarantined versus 3 active — the system caught the wave."

**Query 2 — Bot Wave Alerts Fired:**
```
sentinelai_security_alerts_created_total{alert_type="bot_wave"}
```
Say: "Eight bot wave alerts created across our simulation runs. Each one corresponds to a detected mass registration event."

**Query 3 — Failed Login Attempts:**
```
sentinelai_auth_login_total{status="failed"}
```
Say: "192 failed login attempts tracked during our credential stuffing simulation. Every single one logged, timestamped, with the offending IP recorded."

**Query 4 — API Request Rate (Live):**
```
rate(sentinelai_api_requests_total[1m])
```
Say: "This shows live requests per second to our API, broken down by endpoint. During the attack simulation, you can see the /api/register endpoint spike sharply."

**Query 5 — API Errors:**
```
sentinelai_api_errors_total{endpoint="/api/register",error_code="400"}
```
Say: "116 malformed bot requests to the register endpoint. Our input validation rejected them before they even reached the scoring pipeline."

### 4.2 Grafana Dashboard Walkthrough

Open http://localhost:3001. Log in with admin / admin. Navigate to Dashboards > SentinelAI Overview.

| Panel | What to Say |
|-------|-------------|
| API Request Rate (RPS) | Shows overall platform load in real time |
| RPS by Endpoint | Breaks down which endpoints are being hit hardest |
| Error Rate % | Spikes during bot wave — show the correlation |
| API Latency p95 / p99 | Shows system performance under load — stress test evidence |
| Login Attempts by Outcome | Failed vs OTP vs quarantined vs success |
| Security Rules Triggered | Which specific rules fired most — velocity, email pattern, geo drift |

> **SAY THIS:** "This entire observability stack — Prometheus, Grafana, and PostgreSQL — spins up with a single command: make start-monitoring. Any operator can reproduce this environment in under 2 minutes. This is not a prototype — this is a production-observable system."

---

## SECTION 5: Q&A Preparation

Arindam leads Q&A but any team member can answer questions in their domain. Prepare these answers verbally.

### Security & Architecture Questions

**Q: Why Isolation Forest and not a supervised model?**
"Isolation Forest is unsupervised — it does not need labeled malicious data to train. It learns the shape of normal human behavior and flags deviations. For a new platform like ECLearnix that has no historical attack data, unsupervised detection is the only honest approach. A supervised classifier would require thousands of labeled malicious examples we simply do not have."

**Q: What if a legitimate user types fast and triggers the speed bot rule?**
"The trust score is the sum of multiple independent layers — not a single rule. A fast typist who has a legitimate email, normal mouse movement, a clean IP, and low ML anomaly score will still score above 70 and get direct login. The speed rule alone deducts only 20 points. It takes multiple signals firing together to push a user into quarantine. And if they are wrongly quarantined, the admin can approve them within seconds."

**Q: What about shared campus Wi-Fi where multiple users share one IP?**
"We solved this specifically. The velocity rule applies to registrations from the same IP and the same user agent combination. Students on the same Wi-Fi have different devices, different browsers, different fingerprints. Bots share an identical user agent string. Browser-level device fingerprinting separates legitimate students from bot pools even on a shared gateway."

**Q: How is this different from reCAPTCHA?**
"reCAPTCHA is reactive and visible — the user knows they are being tested and can be trained to bypass it. Our behavioral SDK is invisible and proactive — we have already scored the user before they hit submit. Additionally reCAPTCHA is binary: pass or fail. Our trust score is continuous, which means we apply graduated friction rather than a hard wall. We can also show reCAPTCHA only when the trust score is in the 20 to 40 range — making it one layer of a multi-layer system rather than the only defense."

**Q: How does this scale to thousands of users?**
"We stress-tested PostgreSQL with 50 concurrent workers and 500 simultaneous tasks at pool size 10 with zero failures. The API layer is stateless — every request is independent. Horizontal scaling behind a load balancer is straightforward. The ML model is pre-loaded in memory and each inference takes under 1 millisecond. Prometheus and Grafana give us the observability to detect performance degradation before it becomes a user-facing problem."

**Q: How does the password reset work and is it secure?**
"Three security mechanisms. First, POST /forgot-password always returns 200 regardless of whether the email exists — no email enumeration. Second, the reset token is a 32-byte cryptographically random string, SHA-256 hashed before database storage, so a DB leak does not expose active tokens. Third, tokens are single-use with a 15-minute expiry. Both endpoints have independent rate limits. The flow reuses our existing SMTP infrastructure — same retry logic with exponential backoff and console fallback mode."

### Access Control Questions

**Q: Can a regular user access the admin dashboard?**
"No, through two independent mechanisms. At the frontend, an AdminGuard React component reads the JWT payload on every admin route. If is_admin is false, it redirects to the login page immediately before any dashboard component renders. At the backend, every single admin API route has a require_admin FastAPI dependency that checks the is_admin flag in the database. A 403 Forbidden is returned for non-admin tokens regardless of what the frontend does. These are independent layers — bypassing one does not bypass the other."

**Q: How are admin accounts created?**
"Admin accounts are never created through the public registration form. They are provisioned through a seeding script run once during deployment, or via an environment variable that seeds the first admin on application startup. There is no UI path for a regular user to escalate their own privileges."

**Q: Do admin accounts go through trust scoring?**
"Yes, deliberately. Even admin accounts go through the full trust scoring pipeline on login. A compromised admin credential is actually the highest-risk scenario — so it deserves more scrutiny, not less. If an admin account shows geo drift or unusual behavior, it triggers an alert just like any other account."

### Demo & Testing Questions

**Q: How did you test this without real malicious users?**
"We generated our own attack traffic using custom Python simulation scripts. seed_normal_users.py creates 50 realistic users with human-like behavioral distributions. simulate_attack.py runs three attack scenarios: bot wave, geo drift, and speed bot. The ML model was trained on 300 synthetic feature vectors — 200 benign and 100 malicious — generated by generate_training_data.py with realistic statistical distributions. This is completely standard practice for security systems where you cannot wait for real attacks to occur."

**Q: Your Prometheus metrics show 1,100 alerts. Is that not too many?**
"The 1,100 alert count is from a high-volume stress simulation that included 60 bot-wave registrations, 192 credential stuffing attempts, and multiple error generation waves. In a real production environment, each alert would represent a genuine threat event. The high count in our testing is evidence that the detection system is sensitive and comprehensive, not that it is generating noise — every alert maps to a real simulated attack vector."

---

## SECTION 6: Timing & Final Reminders

| Section | Who | Target Time |
|---------|-----|-------------|
| Opening hook + Slides 1–4 | Arindam | 2.5 minutes |
| Architecture + Stack + Methodology (Slides 5–7) | Atul | 1.5 minutes |
| Backend Implementation (Slide 8 portion + Slide 9) | Atul | 1.5 minutes |
| Security + ML + Results (Slides 8, 9, 10, 11) | Akash | 2.5 minutes |
| Frontend + Screenshots (Slides 13–14) | Debarshi | 2 minutes |
| Testing + Observability + Future (Slides 9, 15, 12) | Parthiv | 1.5 minutes |
| Conclusion (Slide 16) | Arindam | 30 seconds |
| Q&A | All (Arindam leads) | 3 minutes |

### Non-Negotiable Rules for Demo Day

- Never say "we tried to build" or "we planned" — everything is already built and tested. Use past tense for what you built, present tense for how it works.
- Never rely on live manual typing to demonstrate security triggers. Always use pre-seeded accounts or the console override.
- Always point to a specific element when on a screenshot. Name the number, name the panel, name what it means.
- If a judge interrupts, answer briefly, then say "I will cover more on that in a moment" if it is coming in your section.
- If something breaks during the demo, stay calm. Say "Let me show you the same result in our Swagger docs" and use the /api/demo/score endpoint instead.
- Keep the admin dashboard open in a pinned tab throughout the entire demo so you can switch to it instantly.
- Run a full rehearsal end-to-end at least once the night before. Time it.
- Assign a backup person for each demo step — if one person's screen freezes, the backup continues.
- Do not read slides verbatim. Slides are visual anchors. Speak naturally from the script.
- Keep both hands visible on camera at all times. No touching your face, no looking down.

### Browser Tab Setup for Demo Day

- Tab 1 (pinned): http://localhost:3000/login (user login page, start here)
- Tab 2 (pinned): http://localhost:3000/dashboard (admin dashboard, always visible)
- Tab 3: http://localhost:9000/docs (Swagger API docs, backup for API calls)
- Tab 4: http://localhost:9090 (Prometheus, graph tab pre-loaded)
- Tab 5: http://localhost:3001 (Grafana, already logged in, dashboard open)
- Terminal 1: Backend logs (uvicorn output, visible for live feedback)
- Terminal 2 (ready): simulate_attack.py — not yet executed

### Contingency Plans — What to Do When Things Break

**If the backend crashes during the demo:**
FastAPI auto-reloads on file changes. Wait 3 seconds. If it doesn't come back, switch to Terminal 1 and press Ctrl+C then up-arrow + Enter to restart. While it reboots, say: "The server is cycling — this is a normal production behavior. Let me show you the same data in our Swagger docs in the meantime." Open Tab 3 and demonstrate the `/api/demo/score` endpoint with manual parameters.

**If the database connection fails:**
The app defaults to SQLite if Postgres is unreachable. You should see events still flowing. Say: "Our system gracefully degrades to an embedded database — the only thing lost is historical queries until Postgres recovers." Then show the current session data in the admin dashboard.

**If the frontend crashes:**
Refresh the page. If Vite dev server crashed, switch to Terminal 3 and run `make start-frontend` again. While waiting, say: "The frontend is rebuilding — let me show you the same data through our Prometheus metrics." Switch to Tab 4 and run live PromQL queries.

**If the internet goes down (SMTP / GeoIP / external API):**
OTP emails will fail (SMTP dependent). The login flow automatically falls through: if OTP fails to send, the user is logged in with a warning banner. GeoIP defaults to `GEO_LOCAL_MOCK_COUNTRY` (India) when the API is unreachable. Say: "Our system handles offline gracefully — non-critical external dependencies are wrapped in try-catch with sensible defaults."

**If Prometheus or Grafana fails to load:**
Show the `/metrics` endpoint directly at http://localhost:9000/metrics in the browser. Say: "The raw metrics endpoint is always available — Prometheus and Grafana are just visualization layers on top." The raw JSON contains all the same counters.

**If a demo account password is forgotten:**
Open the Swagger docs at http://localhost:9000/docs. Use the GET `/api/demo/score?scenario=legitimate` endpoint to show the scoring pipeline in action without logging in. Say: "Our demo score endpoint simulates what the pipeline would produce for any scenario — you can verify the scoring logic without live credentials." All demo account passwords are documented in Section 1.2.

**If screen sharing fails or lags excessively:**
Send a pre-recorded 5-minute video of the full demo flow to the judges via the hackathon submission portal. Have this video ready before the presentation. If the video was already submitted, say: "The full recorded walkthrough has been submitted alongside this presentation — the data and metrics you see there are from the same live system."

### Rehearsal Countdown

| When | What |
|------|------|
| 7 days before | Assign slides to members. Each person writes their section using the scripts above. |
| 5 days before | First full run-through (no timing, just content flow). Identify gaps. |
| 3 days before | Timed rehearsal with stopwatch. Cut or expand sections to hit 12 minutes. |
| 2 days before | Full rehearsal with screenshots, terminal, and browser switching. Practice handoffs between speakers. |
| 1 day before | Dress rehearsal. Record it. Watch it back. Fix awkward pauses and unclear explanations. |
| Morning of | Run the Setup Checklist (Section 1). Do a dry run of the first 2 minutes and the live demo only. |
| 15 minutes before | Call to the restroom. Drink water. Open all tabs. Confirm all services are running. Breathe. |

### Common Pitfalls to Avoid

- Do NOT click "Send OTP" more than once — the first OTP is invalidated when a new one is generated.
- Do NOT close the terminal running the backend — log output is your debug lifeline.
- Do NOT resize the browser window during the demo — it may trigger React re-renders.
- Do NOT open more than 6 tabs — cognitive load kills demo flow.
- Do NOT trust autocomplete in the console override — type `window.__DEMO_OVERRIDE__` manually.
- Do NOT run `make seed-users` or `seed_normal_users.py` more than once — duplicate users will trigger unique constraint errors.

---

**Good luck, Cipher Sentinels.**

*The system is built. The data is real. The demo is ready. You have everything you need.*
