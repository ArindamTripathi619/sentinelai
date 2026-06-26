# SentinelAI — Judge Q&A Preparation

> Comprehensive answers covering architecture, design decisions, security, ML, scaling, and trade-offs.  
> Prepare for any question the judges might ask.

---

## Table of Contents

1. [Architecture & Design Decisions](#1-architecture--design-decisions)
2. [Trust Score System](#2-trust-score-system)
3. [Behavioral Fingerprinting](#3-behavioral-fingerprinting)
4. [Rules Engine](#4-rules-engine)
5. [ML Model & Training Data](#5-ml-model--training-data)
6. [Security & Authentication](#6-security--authentication)
7. [Database & Persistence](#7-database--persistence)
8. [Scalability & Performance](#8-scalability--performance)
9. [Frontend & Admin Dashboard](#9-frontend--admin-dashboard)
10. [Demo & Presentation](#10-demo--presentation)
11. [Production Readiness & Gaps](#11-production-readiness--gaps)
12. [Team & Collaboration](#12-team--collaboration)

---

## 1. Architecture & Design Decisions

### Q1.1 Why FastAPI and not Django, Flask, or Express?

**Answer:** Three reasons drove the choice:

1. **Async-native.** FastAPI supports `async/await` out of the box, which means the geolocation call to `ip-api.com` (an HTTP call in `geo.py`) doesn't block the entire event loop. With Flask, every external call would block a worker thread.

2. **Automatic validation.** Pydantic models (e.g., `BehavioralPayload` in `scorer.py`) double as request validators. The 5+ behavioral signal fields — `typing_variance_ms`, `time_to_complete_sec`, `mouse_move_count`, `keypress_count`, plus optionals like `mouse_entropy_score` — are validated without a single line of manual `if` check. This eliminated ~30% of boilerplate.

3. **Built-in docs.** Swagger UI at `/docs` and ReDoc at `/redoc` come for free. During integration, Debarshi (frontend) could see the exact request/response shapes without waiting for Atul to write docstrings.

**Stretch (why not Django?):** Django's ORM is richer than SQLAlchemy, but its "batteries-included" philosophy would have meant fighting the framework for a lean security API. We didn't need an admin panel, migrations framework, or templating engine. FastAPI gave us exactly the surface area we needed.

---

### Q1.2 Why four independent penalty layers instead of a single ML model end-to-end?

**Answer:** This was a deliberate architecture decision inspired by how real-world systems (Stripe Radar, Google reCAPTCHA) work — **defense in depth with independent signal sources.**

Each layer has different properties:

| Layer | Deterministic? | Latency | Explainable? | Adversarial Robustness |
|---|---|---|---|---|
| Rules Engine | Yes | <1ms | Fully | Easy to bypass if known |
| Behavioral SDK | Yes (thresholds) | Client-side | Fully | Hard to fake (synthetic signals) |
| ML Model | No (probabilistic) | ~2ms | Partially (feature importance) | Hardest to game |
| Quarantine System | N/A (post-score) | N/A | Fully | N/A |

If we had put everything into a single ML model, we'd lose the ability to:
- **Explain** why a user was flagged ("rule 3 fired" is clear, "anomaly score -0.73" is not)
- **Override** specific rules without retraining (e.g., reducing velocity penalty during a legit marketing campaign)
- **Debug** the system when it misclassifies (we can look at each layer independently)

The penalties stack additively with caps: rules (0-60), behavioral (0-25), ML (0-15). Each cap prevents any single layer from dominating.

---

### Q1.3 Why SQLite by default and Postgres for production? Why not use Postgres in dev too?

**Answer:** Pragmatic hackathon scoping. SQLite is zero-setup — no Docker, no service, no `DATABASE_URL` configuration. A judge can clone the repo, run `pip install -r requirements.txt && uvicorn main:app --reload`, and have a working backend in 30 seconds.

However, the codebase is **Postgres-ready from day one**. The `database.py` engine builder detects the `DATABASE_URL` scheme and adjusts connection parameters accordingly:
```python
if is_sqlite_url(database_url):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 20
```

In production, you set `DATABASE_URL=postgresql+psycopg2://...` and get connection pooling, concurrent writes, and the JSONB capabilities we use in the `events.metadata` column.

---

### Q1.4 What is the middleware ordering and why does it matter?

**Answer:** Middleware in FastAPI is applied in **reverse order of registration** (last added = first executed). Our stack (from outermost to innermost):

```
1. CORSMiddleware          → Handles preflight, CORS headers
2. TrustedHostMiddleware   → Rejects requests with spoofed Host headers
3. RequestTimingMiddleware → Captures duration for Prometheus metrics
4. SecurityHeadersMiddleware → Adds X-Frame-Options, HSTS, XSS-Protection
```

We placed CORS first because preflight `OPTIONS` requests must be handled before any processing. Security headers are innermost because they should be applied even if an earlier middleware returns early. See `backend/main.py:110-132` for the full setup.

---

### Q1.5 Why no Redis or in-memory cache?

**Answer:** The system doesn't need one yet. The critical path is:

1. **Auth requests** — JWT verification is stateless (no cache needed)
2. **Scoring pipeline** — Rules engine is O(n) with n < 10 rules, ML inference is a single tree evaluation (<2ms). Both are faster than a cache round-trip.
3. **Dashboard polling** — 4-second interval already amortizes DB load; adding Redis would increase operational complexity for marginal gain.

If we scaled to 10K+ concurrent users, we'd add Redis for:
- Rate limiter state (currently in-memory via slowapi)
- Session stores (currently DB-based for OTP sessions)
- Dashboard aggregation cache (pre-compute analytics every 10s instead of every 4s per admin)

---

### Q1.6 How did you handle environment configuration across the team?

**Answer:** A single `.env` file at the repository root loaded by `backend/main.py:15`:
```python
load_dotenv(ROOT / '.env')
```
This MUST happen before any module imports that read env vars (e.g., `database.py` reads `DATABASE_URL` at module level). The `.env.example` serves as the canonical reference for all 20+ variables.

The key rule we enforced: **share the `.env.example` in the repo, share the actual values in the team group chat.** This prevented credential leaks while keeping everyone unblocked.

---

## 2. Trust Score System

### Q2.1 Explain the exact trust score formula and why those weights?

**Answer:** The formula is:

```
trust_score = clamp(100 - rule_penalty - behavioral_penalty - ml_penalty, 0, 100)
```

| Component | Range | Rationale |
|---|---|---|
| `rule_penalty` | 0-60 | Rules are hardest evidence (concrete behavioral violations) |
| `behavioral_penalty` | 0-25 | SDK signals are noisier (can be affected by network latency, device type) |
| `ml_penalty` | 0-15 | ML is probabilistic; it augments, not overrides |

The caps prevent any single component from dominating. A user who triggers 3 rules (max 60) can only lose 25 from behavior and 15 from ML — giving a minimum score of 0, never negative.

**The band thresholds** (70/40/20) were chosen based on empirical testing with the seed data:
- >= 70: Normal human variance
- 40-69: Some suspicious signals, warrant OTP
- 20-39: Strong signals, need CAPTCHA + admin attention
- < 20: Overwhelming evidence, quarantine

These are configurable via `TRUST_THRESHOLD_DIRECT_LOGIN`, `TRUST_THRESHOLD_OTP`, and `TRUST_THRESHOLD_QUARANTINE` env vars.

---

### Q2.2 How did you validate the trust score thresholds? What about false positives?

**Answer:** Two validation approaches:

1. **Synthetic validation.** The `seed_normal_users.py` script generates 50 users with human-like behavioral data (typing variance 100-300ms, completion time 20-80s, mouse moves 20-80). These consistently score 70+ (median ~85). The `simulate_attack.py` script generates obvious bots (typing variance <5ms, completion <2s, 0 mouse moves). These score below 20.

2. **Delta check.** The `demo/score` endpoint (`backend/main.py:221`) lets us test any scenario and see the exact penalty breakdown. A legitimate user gets:
   ```
   {trust_score: 82, rule_penalty: 0, behavioral_penalty: 0, ml_penalty: 0}
   ```
   A bot wave user gets:
   ```
   {trust_score: 3, rule_penalty: 45, behavioral_penalty: 15, ml_penalty: 15}
   ```

**False positives:** The quarantine system (threshold <20) is explicitly designed for this — users aren't hard-blocked. They enter a "quarantine" state where an admin reviews and can restore them. This mirrors how Stripe Radar and Cloudflare handle borderline cases.

---

### Q2.3 Does the trust score persist? How does it update over time?

**Answer:** Yes. The `users` table stores `trust_score` as a column (default 100). On each login, `score_login()` in `scorer.py` takes the **existing** trust score as its starting point and subtracts login-specific penalties (geo drift, ML):
```python
trust_score = max(0, min(100, existing_trust_score - total_penalty))
```

This means:
- Normal behavior → score stays high (decays slowly via login penalties)
- Suspicious behavior → score drops immediately
- The score **rises** only through admin intervention (setting status back to active) or a trust repair mechanism (not implemented — stretch goal)

Every score change is logged in the `events` table via `trust_score_at_time`, enabling the forensic timeline to show "this user was at 85, then dropped to 32, then to 15" across their session history.

---

### Q2.4 What trust score decision bands map to which auth outcomes?

**Answer:**

| Band | Login Outcome | API fields |
|---|---|---|
| >= 70 | Direct login | `{token: "eyJ...", otp_required: false, recommendation: "allow"}` |
| 40-69 | OTP required | `{token: null, otp_required: true, otp_session_id: "...", recommendation: "otp"}` |
| 20-39 | CAPTCHA required | `{token: null, captcha_required: true, captcha_prompt: "A3XK9P", recommendation: "captcha"}` |
| < 20 | Quarantined / Blocked | `{token: null, is_blocked: true, is_hard_block: false, recommendation: "quarantine"}` |

The CAPTCHA is a **signed text prompt** — we generate a random alphanumeric string (e.g., "A3XK9P"), base64-encode it with an HMAC signature, and send it to the frontend. The frontend displays it, the user types it back, and the `/api/captcha/verify` endpoint verifies the signature. No external service dependency. See `backend/auth.py:231-260`.

---

## 3. Behavioral Fingerprinting

### Q3.1 What signals does the JS SDK actually capture? How?

**Answer:** The behavioral SDK (`frontend/src/sdk/behavioral.js`, 204 lines) captures 7 signals:

| Signal | Collection Method | Human Range | Bot Range |
|---|---|---|---|
| `typing_variance_ms` | StdDev of `keydown` timestamps | 80-400ms | 0-10ms |
| `time_to_complete_sec` | `startTracking` → `getPayload` delta | 15-120s | 0.5-3s |
| `mouse_move_count` | Throttled `mousemove` (100ms) | 20-200 | 0-2 |
| `keypress_count` | `keydown` total | 50-200 | 20-50 |
| `session_tempo_sec*` | Mean interval across all events | 2-10s | <1s |
| `mouse_entropy_score*` | Shannon entropy of direction buckets | 0.4-0.9 | <0.2 |
| `fill_order_score*` | Unique focus sequence / repetition ratio | 0.7-1.0 | <0.4 |

*Optional fields — collected if available.

The tracking starts on component mount via `useEffect` and stops on unmount. All signals are emitted as a single JSON payload (`behavioralData`) alongside the form submission.

**Demo override:** `window.__DEMO_OVERRIDE__` bypasses real tracking for presentations and returns hardcoded values — useful to demonstrate a specific trust band without typing slowly.

---

### Q3.2 Can't an attacker just fake the behavioral payload? It's client-side JavaScript.

**Answer:** Yes — and we explicitly acknowledge this in the architecture.

The behavioral payload is **one of four layers**, not the sole decision. Even if an attacker sends perfect human-like signals:

1. The **rules engine** still catches velocity, email pattern, and duplicate device fingerprints
2. The **ML model** still sees the full feature vector (including server-side signals the attacker can't fake, like `registrations_from_ip_1h`)
3. The **geolocation check** still detects cross-country login drifts

This is the same approach Google reCAPTCHA uses — client-side signals are weighted, but server-side signals provide the ground truth. Layers 2-4 (rules, ML, quarantine) are all server-side and cannot be tampered with.

---

### Q3.3 How do you handle privacy? What about GDPR/FERPA compliance?

**Answer:** For a hackathon project, we designed the system to minimize data collection by default:

- **No persistent tracking.** Behavioral signals are captured per-session, attached to the request, and never stored as raw data. Only the derived trust score is persisted.
- **No cookies.** The SDK uses no cookies, localStorage only for JWT tokens (cleared on logout).
- **IP addresses** are used transiently for geolocation and velocity detection, stored in the events table for forensic purposes with the explicit understanding this is a security system.

**Stretch (production):** We'd add:
- A data retention policy (purge raw events > 90 days)
- An opt-out mechanism for behavioral tracking
- Encryption at rest for the events table
- A privacy notice in the login page footer (currently shows "Behavioral Profiling Active" as a transparency measure)

---

## 4. Rules Engine

### Q4.1 Walk through all 6 rules and their penalties.

**Answer:**

| Rule | Trigger Condition | Penalty | Alert | Code (`backend/rules.py`) |
|---|---|---|---|---|
| Velocity (IP) | >3 registrations from same IP in 60 min | +25 | `bot_wave` / critical | `check_velocity_ip():88-108` |
| Email Pattern | Disposable domain OR sequential username (user1, test99, 12345, name1234) | +20 | None | `check_email_pattern():111-144` |
| Speed Bot | Registration completed in <3.0 seconds | +20 | `speed_bot` / high | `check_speed_bot():147-169` |
| Duplicate Device | Same User-Agent on >=3 accounts in 24h | +15 | `duplicate_device` / medium | `check_duplicate_device():172-191` |
| Platform Velocity | Registrations per minute > 10 | 0 (alert only) | `velocity_spike` / high | `check_platform_velocity_spike():229-253` |
| Geo Drift | Same user logs in from 2 countries within 120 min | +30 (login only) | `geo_drift` / high | `check_geo_drift():194-226` |

The maximum possible `rule_penalty` a registration can accumulate is 60 (velocity 25 + email 20 + speed 20 + device 15 = 80, but capped at 60 in practice by typical combinations).

---

### Q4.2 How is the disposable domain list maintained? Is it comprehensive?

**Answer:** The core list (`_DISPOSABLE_CORE` in `rules.py:19-46`) contains 40+ well-known disposable domains sourced from public blocklists (mailinator, guerrillamail, yopmail, trashmail, etc.). It's seeded at module load time.

Additionally, the `DISPOSABLE_DOMAINS_EXTRA` env var lets operators extend the list without code changes. Example:
```
DISPOSABLE_DOMAINS_EXTRA=my-temp.com,10minutemail.com,another-domain.com
```

The combined set is built at startup:
```python
DISPOSABLE_DOMAINS = _DISPOSABLE_CORE | ({d.strip().lower() for d in _extra.split(",") if d.strip()} if _extra else set())
```

**Is it comprehensive?** No — there are thousands of disposable domains. In production, you'd subscribe to a maintained blocklist API (e.g., https://github.com/disposable-email-domains/disposable-email-domains) and update daily via CI.

---

### Q4.3 Geo drift detection — how do you handle users who legitimately travel?

**Answer:** The 120-minute window and 30-point penalty are calibrated to distinguish:

- **Session hijacking** — attacker logs in from a different country minutes after the real user
- **Legitimate travel** — user flies from India to Germany but the gap between logins is >2 hours

We also store the `last_country` per user, and the drift is only triggered on **login** (not registration). The penalty is applied to the **login trust score**, not the user's permanent score. After a successful login (with or without OTP), the user's `last_country` is updated to the new country, so the next login from that country won't trigger.

The geo data comes from `ip-api.com` (free, no key) via `geo.py`. For local development (127.0.0.1), we mock a configurable country (`GEO_LOCAL_MOCK_COUNTRY`, default "India").

---

## 5. ML Model & Training Data

### Q5.1 Why Isolation Forest and not a supervised model like Random Forest or XGBoost?

**Answer:** Three reasons, rooted in the hackathon context:

1. **No labeled data required.** Isolation Forest is unsupervised — it learns what "normal" looks like and flags deviations. We didn't need a manually labeled dataset of 10,000 real users. As we say in the docs: *"We trained on observed normal behavior and flag statistical outliers."* That's a completely legitimate real-world approach.

2. **Contamination parameter.** The `contamination=0.1` parameter lets us express "we expect ~10% of users to be anomalous" without hard-coding a threshold. This is configurable via `ML_CONTAMINATION` env var.

3. **Interpretable scores.** The model outputs an anomaly score in [-1, 0] that maps intuitively to a penalty:
   ```python
   ml_penalty = min(int(abs(anomaly_score) * 15), 15)
   ```
   A score of -0.5 → 7 points, -1.0 → 15 points. Simple, transparent.

**Stretch (if asked):** We also trained a Random Forest classifier (Option B in the original plan) which achieved ~96% accuracy on synthetic data, but we chose Isolation Forest for the demo because it doesn't require the "your training data is fake" defense.

---

### Q5.2 Your training data is synthetic. How do we know the model isn't overfitting to fake patterns?

**Answer:** Fair question. Two defenses:

1. **Isolation Forest is robust to this.** Unlike a neural network, an Isolation Forest doesn't memorize training examples. It builds random forests that partition feature space and measures how "shallow" a new point sits in those trees. As long as the **distributions** of synthetic features are reasonable, the model generalizes.

2. **We validated on three distinct profiles.** The training data (`generate_training_data.py`) creates 200 benign samples with **high variance** (normal distributions with realistic stddevs) and 100 malicious samples across **three attack profiles**:
   - Pure bots (tight clusters, extreme values)
   - IP-wave bots (slightly looser)
   - Semi-automated (borderline cases, hardest to detect)

   The sanity check in `ml_model.py:84-88` verifies that malicious samples are flagged:
   ```python
   predicted = model.predict(malicious_features)
   flagged = (predicted == -1).sum()
   print(f"Sanity check: {flagged}/{len(malicious)} malicious samples correctly flagged")
   ```

3. **Real-world validation path.** In production, you'd deploy the model in shadow mode (log predictions but don't act on them), collect ground truth via admin review flags, and retrain quarterly. The architecture supports this — the ML penalty is capped at 15 points specifically so bad model performance doesn't break the system.

---

### Q5.3 How many features does the model use? Can you walk through each?

**Answer:** 7 features, all normalized and order-aligned with `FEATURE_NAMES` in `ml_model.py:16-24`:

| # | Feature | Source | Human | Bot |
|---|---|---|---|---|
| 1 | `typing_variance_ms` | Behavioral SDK | 80-400ms | 0-10ms |
| 2 | `time_to_complete_sec` | Behavioral SDK | 15-120s | 0.5-3s |
| 3 | `mouse_move_count` | Behavioral SDK | 20-200 | 0-2 |
| 4 | `registrations_from_ip_1h` | DB query | 1 | 5-50 |
| 5 | `email_pattern_score` | Rules engine | 0.8-1.0 | 0.0-0.3 |
| 6 | `keypress_count` | Behavioral SDK | 50-200 | 20-50 |
| 7 | `session_actions_per_min` | Behavioral SDK | 2-8 | 20-100 |

Features 1-3 and 6-7 are **client-side** (can be gamed), features 4-5 are **server-side** (can't be faked). This mixes signal types so an attacker who fakes typing perfectly still can't hide their registration velocity.

---

### Q5.4 How is the model loaded and served? What happens during inference failures?

**Answer:** The model is loaded once at server startup via `main.py:283-287`:
```python
ml = load_ml_model()
if ml is not None:
    logger.info("ML model loaded on startup")
else:
    logger.warning("ML model not found — predictions will return neutral scores")
```

During inference, `predict()` in `ml_model.py:102-134` handles every failure mode:
- No model file → returns 0.0 (neutral, no penalty)
- Corrupted model → caught by `joblib.load` exception → returns 0.0
- Missing metadata → falls back to raw `score_samples` normalization

The system is **gracefully degraded** without ML — rules + behavioral still provide 85 points of penalty range. This was a deliberate design choice: ML is additive, not critical path.

---

## 6. Security & Authentication

### Q6.1 How does the progressive auth flow work? Walk through the full login chain.

**Answer:** The full flow for a login:

1. **Client** submits `POST /api/login` with `{email, password, behavioral, ip_address?, user_agent?}`
2. **Backend** (`backend/auth.py`) validates credentials (bcrypt, 12 rounds)
3. **Geo** resolves IP to country via `geo.py` (ip-api.com)
4. **Scoring** calls `score_login()` which:
   - Checks geo drift rule (same user, different country within 120 min)
   - Runs ML inference on user's behavioral vector
   - Computes `new_score = existing_score - rule_penalty - ml_penalty`
5. **Recommendation** maps score to action:
   - >= 70: returns JWT directly (`recommendation: "allow"`)
   - 40-69: creates OTP session, returns `otp_session_id` + `otp_required: true`
   - 20-39: creates HMAC-signed CAPTCHA challenge, returns `captcha_token` + `captcha_prompt`
   - < 20: sets `is_blocked: true` (or `is_hard_block: true` if already blocked)
6. **Client** (frontend `Login.jsx`) checks response fields and renders the appropriate sub-form
7. **Progressive resolution:**
   - OTP → `POST /api/otp/verify` → JWT
   - CAPTCHA → `POST /api/captcha/verify` → JWT
   - Quarantine → block message with admin review note

All auth events are logged to the `events` table with `trust_score_at_time`, enabling the forensic timeline.

---

### Q6.2 How is the JWT handled? What's the expiry and signing algorithm?

**Answer:**
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiry:** 24 hours (configurable via `JWT_EXPIRE_HOURS` env var)
- **Payload:** `{sub: user_id, email, is_admin, exp, iat}`
- **Storage:** `localStorage` under key `sentinelai_token`
- **Frontend interceptor:** `api.js` attaches `Authorization: Bearer <token>` to every request. A 401 response clears all session data and redirects to `/login`.

The `isAdmin()` check on the frontend decodes the JWT base64 payload:
```javascript
const payload = JSON.parse(atob(token.split('.')[1]));
return payload.is_admin === true;
```

The backend's `AdminGuard` also verifies JWT expiry server-side. This is important because a tampered token would pass the client-side check but fail on the actual API call.

---

### Q6.3 What rate limiting is in place?

**Answer:** We use `slowapi` with the `get_remote_address` key function:

| Endpoint | Rate Limit | Rationale |
|---|---|---|
| `POST /api/register` | 5/min/IP | Prevent mass account creation |
| `POST /api/login` | 10/min/IP | Throttle brute force attempts |
| `POST /api/forgot-password` | 3/min/IP | Prevent email bombing |
| `POST /api/reset-password` | 5/min/IP | Throttle token brute force |

Rate limiter key defaults to `get_remote_address` which reads `request.client.host`. Behind proxies, this should be adjusted to read `X-Forwarded-For`.

---

### Q6.4 How are passwords stored? What hashing algorithm?

**Answer:** bcrypt with 12 salt rounds via `backend/auth.py`:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_password(password)  # Uses 12 rounds by default
```

The 12 rounds (~250ms per hash) is the standard security-comfort tradeoff. Each hash includes a unique salt automatically (bcrypt's built-in feature). No plaintext passwords are ever stored.

---

### Q6.5 How does the CAPTCHA work without an external service?

**Answer:** It's a **signed text challenge** — no external dependency needed:

1. **Generation** (`_create_captcha_challenge` in `auth.py:231`):
   - Generate a random 6-char alphanumeric string (e.g., "A3XK9P")
   - Compose payload: `f"{user_id}:{prompt}:{expiry_timestamp}"`
   - Sign with HMAC-SHA256 using `JWT_SECRET`: `base64(hmac.sign(payload)) + "." + base64(payload)`
   - Return `captcha_token` (signed) + `captcha_prompt` (plain text)

2. **Verification** (`_verify_captcha_challenge` in `auth.py:246`):
   - Decode base64 token
   - Verify HMAC signature (rejects tampered tokens)
   - Check expiry (5 minute window)
   - Compare user's answer against prompt (case-insensitive)
   - Return `user_id` if valid, raise `ValueError` otherwise

This is stateless — no DB storage needed for CAPTCHA sessions. The token carries everything needed for verification.

---

### Q6.6 Security headers — what's covered?

**Answer:** Added via `SecurityHeadersMiddleware` in `backend/main.py:95-108`:

| Header | Value | Prevents |
|---|---|---|
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing |
| `X-XSS-Protection` | `1; mode=block` | Reflected XSS (legacy browsers) |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | SSL stripping |
| `Set-Cookie` | `SameSite=Strict` | CSRF (cookie-based attacks) |

Plus: `TrustedHostMiddleware` prevents Host header injection attacks. CORS is restricted to `FRONTEND_URL` (default `http://localhost:3000`).

---

## 7. Database & Persistence

### Q7.1 What's the schema? How many tables?

**Answer:** 4 tables defined in `backend/models.py`:

1. **`users`** — `id` (UUID), `email` (unique), `password_hash`, `trust_score` (default 100), `status` (active/quarantined/blocked), `registered_at`, `last_login_at`, `last_ip`, `last_country`, `is_admin`

2. **`events`** — `id` (UUID), `user_id` (FK), `action` (register/login/login_failed/otp_sent/etc.), `ip_address`, `country`, `user_agent`, `trust_score_at_time`, `timestamp`, `metadata` (JSON text)

3. **`alerts`** — `id` (UUID), `type` (bot_wave/geo_drift/speed_bot/etc.), `severity` (low/medium/high/critical), `description`, `affected_user_ids` (JSON array), `resolved`, `timestamp`

4. **`otp_sessions`** — `id` (UUID), `user_id` (FK), `otp_code`, `expires_at`, `used`

Primary keys are UUID strings generated via `models.new_id()` (Python `uuid4`). This avoids sequential ID enumeration attacks and simplifies distributed ID generation.

---

### Q7.2 How are the velocity queries implemented? Are they efficient?

**Answer:** Velocity is checked by querying the `events` table with `GROUP BY` and counting:
```python
registrations_from_ip_last_hour = db.query(func.count(Event.id)).filter(
    Event.action == "register",
    Event.ip_address == ip_address,
    Event.timestamp >= datetime.utcnow() - timedelta(hours=1)
).scalar() or 0
```

For a hackathon project with <10K events, even a full table scan completes in <50ms on SQLite. With the composite indexes mentioned in `914406d`, this drops to <2ms on Postgres.

The platform velocity spike uses a similar query with a 1-minute window:
```python
registrations_per_minute = db.query(func.count(Event.id)).filter(
    Event.action == "register",
    Event.timestamp >= datetime.utcnow() - timedelta(minutes=1)
).scalar() or 0
```

---

### Q7.3 Why doesn't the schema use foreign key constraints in SQLite?

**Answer:** It does — but SQLite requires `PRAGMA foreign_keys = ON` per connection, which the SQLAlchemy engine doesn't enable by default. The schema defines FKs:
```sql
FOREIGN KEY (user_id) REFERENCES users(id)
```

With PostgreSQL (which enforces FKs by default), referential integrity is guaranteed. For SQLite, we enforce integrity at the application layer. This trade-off was acceptable for a hackathon.

---

## 8. Scalability & Performance

### Q8.1 How many concurrent users could this handle? Where's the bottleneck?

**Answer:** For a campus-scale platform (<10K users, <100 concurrent), the current architecture handles it trivially. Bottlenecks by component:

- **FastAPI (Uvicorn):** ~10K requests/second per worker on a single core. Not the bottleneck.
- **Rules Engine:** O(n) with n < 10 rules. <1ms per request. Not the bottleneck.
- **ML Inference:** ~2ms per request (single tree evaluation). Not the bottleneck.
- **Database (SQLite):** Single-writer, ~50 concurrent reads before contention. **This is the bottleneck.**
- **Geolocation API:** Network-bound (ip-api.com, ~100ms). **This is the bottleneck for login.**

**Scaling plan:**
1. Swap SQLite → Postgres (already supported, just change `DATABASE_URL`)
2. Add connection pooling (already configured: pool_size=20, max_overflow=20 in `database.py`)
3. Cache geolocation results (same IP → same country, TTL 1 hour)
4. Add Redis for rate limiter state (slowapi supports this)
5. Horizontally scale backend behind a load balancer (FastAPI is stateless)

---

### Q8.2 How would you handle 100K users?

**Answer:** In order of priority:

1. **Database:** Postgres with read replicas. The events table would be the largest (100K users × 50 events/user = 5M rows). Add time-based partitioning (monthly partitions) and an index on `(user_id, timestamp)`.
2. **Dashboard polling:** Currently polls every 4 seconds. At 100 admins, that's 25 dashboard requests/second. Pre-compute analytics snapshots every 10 seconds and serve from cache.
3. **ML inference:** Pre-compute feature vectors and batch-predict via a background scheduler (Celery/APScheduler) instead of real-time inference.
4. **Geolocation:** Replace ip-api.com with a local GeoIP database (MaxMind GeoLite2) — eliminates network latency and rate limits.
5. **Rate limiter:** Move from in-memory slowapi to Redis-backed rate limiting.

---

### Q8.3 The dashboard polls every 4 seconds — is that sustainable?

**Answer:** At a hackathon scale, yes. Each poll is 5 parallel requests (summary, velocity, trust-distribution, users, alerts). Each request is a simple SQL query or aggregation. On SQLite with <500 users, response times are <20ms.

For production:
- Add ETags or `Last-Modified` headers so the frontend can skip re-rendering unchanged data
- Switch to Server-Sent Events (SSE) for real-time push
- Pre-compute KPI summaries every 10 seconds in a background task

---

## 9. Frontend & Admin Dashboard

### Q9.1 Why no TypeScript? Isn't that standard for React projects?

**Answer:** Two reasons:

1. **Team velocity.** Two of our five members (Debarshi and Parthiv) had limited TypeScript experience. For a 12-hour hackathon, the cost of type errors was lower than the cost of learning TS.

2. **Project size.** With 2,290 combined lines across 10 JSX components, the type surface is small enough to manage manually. The behavioral SDK (`204 lines`), API layer (`68 lines`), and Tailwind config (`81 lines`) are all independently verified by manual testing.

**Stretch (if asked):** We'd add TypeScript for any production deployment. The existing JSDoc comments (`// @param {string} email`) already document the critical interfaces.

---

### Q9.2 What's the dashboard architecture? How does it get live data?

**Answer:** The dashboard (`Dashboard.jsx`, 699 lines) uses a **recursive setTimeout** polling pattern (not `setInterval`, which can stack):
```javascript
useEffect(() => {
    let mounted = true;
    let timer;

    const fetchAll = async () => {
        const [summary, velocity, dist, users, alerts] = await Promise.all([...]);
        if (mounted) timer = setTimeout(fetchAll, 4000);
    };

    fetchAll();
    return () => { mounted = false; clearTimeout(timer); };
}, []);
```

The 5 parallel requests:
- `GET /api/analytics/summary` — KPI cards (Total Users, Avg Trust Score, Active Alerts, Threats Detected)
- `GET /api/analytics/velocity?window=X&bucket=Y` — Registration velocity chart
- `GET /api/analytics/trust-distribution` — Trust score donut chart
- `GET /api/users` — Users table (paginated, searchable)
- `GET /api/alerts?limit=15` — Active alerts panel

All requests happen in parallel via `Promise.all`. A single 401 triggers session clear and redirect.

---

### Q9.3 What charts are used and why those specific visualizations?

**Answer:** Both from Recharts:

1. **Request Velocity** — `LineChart` with monotone interpolation. Shows registrations over time with configurable windows (1H/6H/24H/7D). The line graph is best for showing trends and spikes. When a velocity spike triggers, the chart shows a visible upward jump.

2. **Trust Distribution** — `PieChart` donut (innerRadius=32, outerRadius=52). Shows the count per trust band (70+/40-69/20-39/0-19). The donut is compact (fits in 4 columns) and the center shows total node count.

Both charts have:
- Custom dark-themed tooltips
- No axis lines (cyber aesthetic)
- Gradient fills matching the color palette
- Graceful empty state (gray fallback for no data)

---

## 10. Demo & Presentation

### Q10.1 Is the demo fully live? What's scripted vs real?

**Answer:** The demo is a **hybrid** — standard practice for security demos:

**Live (real-time, unscripted):**
- The `simulate_attack.py` script runs live during the presentation
- The dashboard polls every 4 seconds and shows alerts appearing
- Admin can click any user and see their forensic timeline
- Each login attempt hits the actual scoring pipeline

**Seeded (prepared before the demo):**
- 50 normal users via `seed_normal_users.py` (creates a "green" baseline)
- 12 demo dashboard users via `seed_demo_dashboard.py` (across all trust bands)

The attack script runs live with colorful terminal output showing each registration attempt and the resulting trust score. Judges watch the dashboard react in real time — this is what makes it impressive.

---

### Q10.2 What if the API call to ip-api.com fails during the demo?

**Answer:** The system degrades gracefully. In `geo.py:67-69`:
```python
except Exception as e:
    print(f"[geo.py] Failed to geolocate {ip}: {e}")
    return None
```

When geolocation fails, `get_country()` returns `"Unknown"`. The geo drift rule (`rules.py:208`) checks `if last_country is None` and skips the check. The login proceeds with a lower total penalty (no geo drift penalty). The trust score is still computed from the remaining layers.

For demo reliability, we also have `127.0.0.1` mocked to return `GEO_LOCAL_MOCK_COUNTRY` (default India), so local demos never fail.

---

### Q10.3 Can you walk through what happens when you run `simulate_attack.py --scenario botwave`?

**Answer:**

1. **Script** generates 15 user accounts (`user1@temp.com` through `user15@temp.com`) with:
   - Bot-like behavioral data (typing_variance_ms ≈ 4, time_to_complete_sec ≈ 1.1, mouse_move_count = 0)
   - All from the same IP address (`45.118.144.200`)
   - All from the same User-Agent string

2. **Each registration** hits `POST /api/register` with the payload. The scoring pipeline runs:
   - **Velocity rule:** 15 registrations from same IP > limit of 3 → +25 penalty, `bot_wave` alert created
   - **Email pattern:** `user1@temp.com` matches sequential pattern + disposable domain `temp.com` → +20 penalty
   - **Speed bot:** 1.1s < 3.0s threshold → +20 penalty
   - **Behavioral:** 0 mouse moves → +5, typing variance 4ms → +10
   - **Total penalty:** ~80 → trust score ≈ 20 → `recommendation: "captcha"`

3. **Dashboard** poll picks up the new alerts within 4 seconds:
   - Active Alerts KPI increments
   - Alerts panel shows "Bot wave detected" with severity critical
   - Velocity chart spikes
   - Users table shows 15 new quarantined users

---

## 11. Production Readiness & Gaps

### Q11.1 What's missing for production? What would you add?

**Answer:** We've documented what's NOT implemented in `AGENTS.md`. Key gaps:

1. **Pre-commit hooks & linter** — No `.eslintrc` or Ruff configuration. We'd add pre-commit with `ruff check` and `prettier` for Python and JSX respectively.

2. **CI/CD** — No GitHub Actions workflows. We'd add a matrix build (Python 3.10/3.11/3.12, Node 18/20) running `project_suite.py` + `npm build`.

3. **Dockerfile** — README mentions one but none exists. We'd add a multi-stage `backend/Dockerfile` and `frontend/Dockerfile`.

4. **Alembic migrations** — Tables are auto-created via `Base.metadata.create_all()`. Production needs schema migration management.

5. **HTTPS** — `Strict-Transport-Security` header is set (line 105) but the backend runs on HTTP. Production would need a reverse proxy (nginx/Caddy) with TLS termination.

6. **Monitoring alerts** — Prometheus metrics are emitted (`/metrics` endpoint) but no alert rules are configured. We'd add Alertmanager rules for bot_wave spikes.

7. **Data retention** — No event purge mechanism. Events table would grow unbounded. We'd add a cleanup job (DELETE events WHERE timestamp < NOW() - 90d).

---

### Q11.2 How would you handle secrets management in production?

**Answer:** Currently, secrets are stored in `.env`. Production would use:

1. **Environment-specific secret stores** — HashiCorp Vault, AWS Secrets Manager, or Doppler
2. **Non-default JWT secret** — The code defaults to `your_super_secret_key_here` which would be catastrophic in production. We've noted this in `AGENTS.md`: "JWT default hard-fails in non-dev environments"
3. **SMTP credentials** — Separated by environment (dev Gmail account vs production transactional email service)
4. **Database passwords** — Rotated on a schedule, injected via container secrets

---

### Q11.3 The ML model file (`ml_model.pkl`) is tracked in git. Is that intentional?

**Answer:** Yes, for a hackathon — it lets judges clone and run without retraining. The model is small (~200KB, Isolation Forest).

In production, you would:
1. Add `*.pkl` to `.gitignore`
2. Store model artifacts in S3/GCS/Blob Storage with versioning
3. Load the model from the storage URL via the `ML_MODEL_PATH` env var
4. Use CI/CD to retrain and push new model artifacts

---

## 12. Team & Collaboration

### Q12.1 Who built what? How did you divide the work?

**Answer:** The team followed a branch-per-owner strategy as documented in `docs/PLAN.md`:

| Member | Branch | Responsibility |
|---|---|---|
| **Arindam** (Tech Lead) | `main` (PR reviews) | Architecture, integration, demo, repo setup |
| **Atul** | `feature/backend-core` | FastAPI core, auth, OTP, database, JWT |
| **Akash** | `feature/security-engine` | Rules engine, ML model, trust scorer, alerts |
| **Debarshi** | `feature/admin-dashboard` | React dashboard, login/register pages, charts, behavioral SDK |
| **Parthiv** | `feature/scripts-and-docs` | Seed scripts, attack simulation, geo.py, training data, docs |

The API contract (`API.md`) was established in Hour 1 to unblock everyone. Arindam reviewed and merged PRs within 30 minutes to maintain velocity.

---

### Q12.2 What was the hardest technical challenge?

**Answer:** **Integration.** Despite having the API contract, three issues emerged during merge:

1. **Field name mismatches.** The behavioral payload was being sent as `behavioralData` (camelCase) from the frontend but expected as `behavioral` (snake_case) by the backend. Fixed by accepting both keys (`backend/AGENTS.md`).

2. **IP resolution.** The frontend was sending `ip_address` in the payload, but the backend also tried `request.client.host`. During local dev, this was always `127.0.0.1`. The resolution order became: `X-Forwarded-For` header → `payload.ip_address` → `request.client.host`.

3. **Trust score alignment.** The dashboard was expecting `bot_waves_detected` but the backend was returning `flagged_today` with a different aggregation. This required coordination between Debarshi (frontend) and Akash (backend) to reconcile the KPI naming.

These are documented in `AGENTS.md` under "Key quirks" — lessons learned that we'd fix upfront in a second iteration.

---

### Q12.3 What would you do differently if you had another 12 hours?

**Answer:** In priority order:

1. **Complete the Events page** — Currently a placeholder ("under construction"). Real event listing for non-admin users.
2. **Trust repair mechanism** — Let users restore their trust score by completing challenges (reCAPTCHA-style gradual trust building).
3. **Admin notification system** — Email/Slack alerts when critical alerts fire (currently only visible on dashboard).
4. **More attack scenarios** — Credential stuffing simulation, session replay detection, simultaneous login detection.
5. **End-to-end tests** — Playwright/Cypress tests for the full auth flow (register → login → OTP → dashboard).

---

## Appendix A: Quick Reference — Key Files

| File | Purpose | Lines |
|---|---|---|
| `backend/main.py` | FastAPI app, middleware, routes, startup | 318 |
| `backend/auth.py` | JWT, OTP, CAPTCHA, password hashing, auth endpoints | ~600 |
| `backend/scorer.py` | Trust score calculation, recommendation mapping | 191 |
| `backend/rules.py` | 6 security rules with penalties and alerts | 320 |
| `backend/ml_model.py` | Isolation Forest training and inference | 168 |
| `backend/models.py` | SQLAlchemy ORM models (4 tables) | ~80 |
| `backend/database.py` | Engine builder, connection pooling | 40 |
| `backend/geo.py` | IP geolocation via ip-api.com | 93 |
| `frontend/src/sdk/behavioral.js` | Client-side behavioral signal collection | 204 |
| `frontend/src/dashboard/Dashboard.jsx` | Admin command center (5 panels) | 699 |
| `frontend/src/auth/Login.jsx` | Login with progressive auth flow | 369 |
| `scripts/seed_normal_users.py` | 50-user baseline seeder | 166 |
| `scripts/simulate_attack.py` | 3 live attack scenarios | ~270 |
| `scripts/generate_training_data.py` | 300-sample synthetic training data | 119 |

## Appendix B: Quick Reference — Key Commands

```bash
# Install
make install

# Start backend (terminal 1)
make start-backend

# Start frontend (terminal 2)
make start-frontend

# Seed baseline users (before demo)
make seed-users

# Run all attacks (live demo)
make attack-all

# Test suite
make test

# Retrain ML model
make train-model
```

---

*Prepared for SentinelAI — Behavioral Intelligence Platform for Campus Event Ecosystems*  
*Built for ECLearnix & All College Event — Hackathon Submission, Domain 5: Cyber Security & Forensic Science*  
*MIT License — Copyright (c) 2026 SentinelAI Contributors*
