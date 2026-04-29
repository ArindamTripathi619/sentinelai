# 🏗️ SentinelAI — System Architecture

## Overview

SentinelAI uses a **layered defense architecture** where every user interaction passes through multiple security checks before being trusted. Rather than blocking users based on a single rule, every decision is driven by a **continuous Trust Score (0–100)** that aggregates signals from four independent layers.

---

## Trust Score Formula

```
trust_score = 100
            - rule_penalty        (0–60 points, from rules engine)
            - behavioral_penalty  (0–25 points, from JS SDK signals)
            - ml_penalty          (0–15 points, from Isolation Forest)
```

The score is clamped to [0, 100]. Each layer can independently contribute penalties.

### Trust Score Bands

| Score | Band | System Action |
|---|---|---|
| 80–100 | ✅ Safe | Direct login, no friction |
| 60–79 | 🟡 Caution | Logged, monitored |
| 40–59 | 🟠 Suspicious | OTP required |
| 20–39 | 🔴 High Risk | OTP + CAPTCHA + admin alert |
| 0–19 | ⛔ Critical | Quarantine, login blocked |

---

## Layer 1 — Behavioral Fingerprinting (Frontend)

A lightweight JavaScript SDK (`behavioral.js`) runs silently on all auth pages and collects:

| Signal | How Collected | Why It Matters |
|---|---|---|
| `typing_variance_ms` | StdDev of keypress intervals | Bots type at perfectly uniform speed |
| `time_to_complete_sec` | Form focus → submit timestamp | Bots complete forms in <2 seconds |
| `mouse_move_count` | `mousemove` event count | Bots rarely move the mouse |
| `keypress_count` | Total keypresses | Detects autofill vs manual typing |

This data is sent as a hidden payload alongside the registration/login form submission. Users never see it.

**Penalty Calculation:**
- `time_to_complete_sec < 3` → -15 points
- `typing_variance_ms < 20` → -10 points  
- `mouse_move_count == 0` → -5 points

---

## Layer 2 — Rules Engine (Backend)

Fast, deterministic rules that fire immediately on every registration or login event.

### Rule: Velocity (IP-based)
```
IF registrations_from_same_ip_in_last_60min > 3:
    penalty += 25
    create_alert(type="bot_wave", severity="critical")
```

### Rule: Email Pattern
```
IF email matches regex /user\d+@/ OR domain in disposable_domains_list:
    penalty += 20
```

### Rule: Speed Bot
```
IF time_to_complete_sec < MIN_REGISTRATION_SECONDS (default: 4):
    penalty += 20
```

### Rule: Duplicate Device
```
IF same user_agent string seen on 3+ different accounts in 24h:
    penalty += 15
```

### Rule: Platform Velocity Spike
```
IF registrations_per_minute > VELOCITY_PLATFORM_LIMIT (default: 10):
    create_alert(type="velocity_spike", severity="high")
    # Does not directly penalize individual users
```

### Rule: Geospatial Drift
```
IF same user_id logs in from country_A, then country_B within 120 minutes:
    penalty += 30 (applied to login trust, not registration)
    create_alert(type="geo_drift", severity="high")
```

---

## Layer 3 — ML Anomaly Detection (Isolation Forest)

An unsupervised anomaly detection model trained on behavioral feature vectors of legitimate users. It learns what "normal" looks like and flags statistical outliers.

### Feature Vector (7 dimensions)
```python
features = [
    typing_variance_ms,           # Human: 80-400ms, Bot: 0-10ms
    time_to_complete_sec,         # Human: 15-120s,  Bot: 0.5-3s
    mouse_move_count,             # Human: 20-200,   Bot: 0-2
    registrations_from_ip_1h,     # Human: 1,        Bot: 5-50
    email_pattern_score,          # Human: 0.8-1.0,  Bot: 0.0-0.3
    keypress_count,               # Human: 50-200,   Bot: 20-50
    session_actions_per_min       # Human: 2-8,      Bot: 20-100
]
```

### Training Data
Generated synthetically by `scripts/generate_training_data.py`:
- 200 benign user vectors (varied, human-like distributions)
- 100 malicious vectors (tight, bot-like distributions)
- Saved as `training_data.csv`

### Model Output
The Isolation Forest returns an **anomaly score** in range [-1, 0]:
- Close to 0 → normal behavior
- Close to -1 → strong anomaly

This is mapped to a penalty:
```python
ml_penalty = max(0, int(abs(anomaly_score) * 15))
```

### Model File
Saved as `backend/ml_model.pkl` using joblib. Re-train with:
```bash
python scripts/generate_training_data.py
python backend/ml_model.py --train
```

---

## Layer 4 — Quarantine System

Users who fall below the quarantine threshold (default: 20) are not hard-banned. Instead:

1. Their account status is set to `quarantined`
2. Login is blocked with a generic "under review" message
3. Their actions are logged at maximum verbosity
4. An alert appears in the admin dashboard for human review
5. An admin can approve (→ `active`) or permanently block (→ `blocked`) them

This avoids false-positive hard bans while keeping the platform safe.

---

## Data Flow Diagram

```
User submits form
      │
      ▼
[behavioral.js SDK]
  Captures: typing variance, mouse moves, form time
  Attaches to request payload
      │
      ▼
POST /api/register or /api/login
      │
      ├──▶ [Rules Engine]
      │       Checks: velocity, email pattern, speed, device fingerprint
      │       Output: rule_penalty (0-60), triggered_rules[], alerts[]
      │
      ├──▶ [Behavioral Scorer]
      │       Processes: SDK payload signals
      │       Output: behavioral_penalty (0-25)
      │
      ├──▶ [ML Model]
      │       Input: 7-dim feature vector
      │       Output: anomaly_score → ml_penalty (0-15)
      │
      ▼
[Trust Score Calculator]
  trust_score = 100 - rule_penalty - behavioral_penalty - ml_penalty
  Determines: action (login / OTP / quarantine)
      │
      ├──▶ [Event Logger] → SQLite events table
      ├──▶ [Alert Writer] → SQLite alerts table (if rules fired)
      └──▶ [API Response] → Frontend
```

---

## Database Schema

### `users`
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    trust_score INTEGER DEFAULT 100,
    status TEXT DEFAULT 'active',  -- active | quarantined | blocked
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    last_ip TEXT,
    is_admin BOOLEAN DEFAULT FALSE
);
```

### `events`
```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,          -- register | login | login_failed | otp_sent | ...
    ip_address TEXT,
    country TEXT,
    user_agent TEXT,
    trust_score_at_time INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,                 -- JSON blob for extra context
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### `alerts`
```sql
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,            -- bot_wave | geo_drift | speed_bot | ...
    severity TEXT NOT NULL,        -- low | medium | high | critical
    description TEXT,
    affected_user_ids TEXT,        -- JSON array of user IDs
    resolved BOOLEAN DEFAULT FALSE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### `otp_sessions`
```sql
CREATE TABLE otp_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE
);
```

---

## External Services

| Service | Purpose | API Key Required |
|---|---|---|
| ip-api.com | IP geolocation | ❌ Free, no key |
| Gmail SMTP | OTP delivery | ✅ App password only |
| Cloudflare Turnstile | CAPTCHA (optional) | ✅ Free key from dashboard |

---

## How the Demo Works

The live demo uses two scripts:

**`seed_normal_users.py`** — Pre-populates the database with 50 realistic users before the presentation.

**`simulate_attack.py`** — Runs 3 attack scenarios live during the presentation:

1. **Bot Wave:** Registers 15 accounts in 8 seconds → velocity alert fires, all quarantined
2. **Geo Drift:** Logs in as a seeded user from India, then immediately from a German IP → geo drift alert fires
3. **Speed Bot:** Completes registration in 1.2 seconds with 0 mouse moves → speed bot + behavioral rules fire

All three scenarios are visible in real time on the admin dashboard.

---

*Maintained by Arindam (Tech Lead) and Parthiv (Docs)*
