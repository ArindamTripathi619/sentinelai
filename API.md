# 📡 SentinelAI — API Contract

> **This document is the source of truth for all endpoints.**  
> Frontend (Debarshi) and Scripts (Parthiv) should build against this contract  
> even before Atul's backend is complete — use mock data in the meantime.

Base URL (local): `http://localhost:9000/api`

---

## 🔐 Authentication Endpoints

### POST `/api/register`
Register a new user. Accepts behavioral payload alongside credentials.

Rate limit: 5 requests/minute/IP

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "behavioral": {
    "typing_variance_ms": 145,
    "time_to_complete_sec": 38,
    "mouse_move_count": 47,
    "keypress_count": 92
  }
}
```

The `behavioral` object also accepts these optional fields:
`sessions_tempo_sec`, `mouse_entropy_score`, `fill_order_score`.

**Response — 200 OK:**
```json
{
  "message": "Registration successful",
  "trust_score": 82,
  "status": "active",
  "triggered_rules": [],
  "rule_penalty": 0,
  "behavioral_penalty": 0,
  "ml_penalty": 0,
  "recommendation": "allow"
}
```

If trust score < 40, user is created with `status: "quarantined"` but the endpoint **still returns 200** with the same shape.

**Response — 400 Bad Request:**
```json
{
  "detail": "Missing email or password"
}
```

---

### POST `/api/login`
Login endpoint. Returns token or triggers progressive auth (OTP → captcha → block) based on trust score.

Rate limit: 10 requests/minute/IP

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ..."
}
```

**Response — 200 OK (high trust, direct login, `>= 70`):**
```json
{
  "token": "eyJhbGci...",
  "token_type": "bearer",
  "trust_score": 85,
  "otp_required": false,
  "user_id": "uuid-string",
  "recommendation": "allow"
}
```

**Response — 200 OK (medium trust, OTP required, `40–69`):**
```json
{
  "token": null,
  "trust_score": 52,
  "otp_required": true,
  "otp_session_id": "temp-session-uuid",
  "user_id": "uuid-string",
  "recommendation": "otp"
}
```

**Response — 200 OK (low trust, CAPTCHA required, `20–39`):**
```json
{
  "token": null,
  "trust_score": 25,
  "captcha_required": true,
  "captcha_token": "base64-signed-challenge",
  "captcha_prompt": "A3XK9P",
  "user_id": "uuid-string",
  "recommendation": "captcha"
}
```

**Response — 200 OK (quarantined/blocked, `< 20`):**
```json
{
  "token": null,
  "trust_score": 12,
  "otp_required": false,
  "is_blocked": true,
  "is_hard_block": false,
  "user_id": "uuid-string",
  "recommendation": "quarantine",
  "message": "Account under review. An admin will review your account status."
}
```
If the user was already `blocked` before this login, `is_hard_block` is `true` and the message changes to `"Account suspended."`.

**Response — 401 Unauthorized (wrong credentials):**
```json
{
  "detail": "Invalid email or password"
}
```

---

### POST `/api/captcha/verify`
Verify a CAPTCHA challenge and receive a JWT token. Used after login returns `captcha_required: true`.

**Request Body:**
```json
{
  "captcha_token": "base64-signed-challenge",
  "captcha_answer": "A3XK9P"
}
```

**Response — 200 OK:**
```json
{
  "token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "uuid-string",
  "message": "Captcha verified successfully"
}
```

**Response — 400 Bad Request:**
```json
{
  "detail": "Missing captcha_token or captcha_answer"
}
```

CAPTCHA tokens expire in 300 seconds (5 minutes).

---

### POST `/api/otp/send`
Send OTP to the user's registered email.

**Request Body:**
```json
{
  "otp_session_id": "temp-session-uuid",
  "email": "user@example.com"
}
```

**Response — 200 OK:**
```json
{
  "message": "OTP sent successfully",
  "expires_in_seconds": 300,
  "delivery_status": "sent",
  "delivery_attempts": 1
}
```

If `SMTP_STRICT_MODE=1` and delivery fails, returns **503** instead.

---

### POST `/api/otp/verify`
Verify the OTP entered by the user and receive a JWT token.

**Request Body:**
```json
{
  "otp_session_id": "temp-session-uuid",
  "otp_code": "847291"
}
```

**Response — 200 OK:**
```json
{
  "token": "eyJhbGci...",
  "token_type": "bearer",
  "user_id": "uuid-string",
  "message": "Login successful"
}
```

**Response — 400 Bad Request:**
```json
{
  "detail": "Invalid or expired OTP"
}
```
Other possible `detail` values: `"OTP already used"`, `"OTP expired"`, `"Invalid OTP code"`, `"Invalid OTP session"`.

---

### POST `/api/forgot-password`
Request a password reset email. Always returns 200 to prevent email enumeration.

Rate limit: 3 requests/minute/IP

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response — 200 OK:**
```json
{
  "message": "If that email is registered, you will receive a reset link."
}
```

Reset tokens expire in 15 minutes.

---

### POST `/api/reset-password`
Verify reset token and update password. Token is the raw token from the reset email.

Rate limit: 5 requests/minute/IP

**Request Body:**
```json
{
  "token": "raw-token-from-reset-email",
  "new_password": "newSecurePassword123"
}
```

**Response — 200 OK:**
```json
{
  "message": "Password reset successful. You can now log in with your new password."
}
```

**Response — 400 Bad Request:**
```json
{
  "detail": "Invalid or expired reset token."
}
```

---

## 👥 User Endpoints (Admin Only — Requires JWT)

### GET `/api/users`
Get all users with their trust scores and status.

**Headers:** `Authorization: Bearer <token>`

**Query Params (optional):**
- `status` — filter by `active`, `quarantined`, `blocked`
- `min_trust` / `max_trust` — filter by trust score range
- `limit` — default 50
- `offset` — for pagination

**Response — 200 OK:**
```json
{
  "total": 134,
  "users": [
    {
      "user_id": "uuid-string",
      "email": "user@example.com",
      "trust_score": 82,
      "status": "active",
      "registered_at": "2025-04-15T10:23:00Z",
      "last_login_at": "2025-04-16T08:11:00Z",
      "last_ip": "203.0.113.42",
      "flag_count": 0
    }
  ]
}
```

---

### GET `/api/users/{user_id}`
Get a single user's full profile.

**Response — 200 OK:**
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "trust_score": 34,
  "status": "quarantined",
  "registered_at": "2025-04-15T10:23:00Z",
  "behavioral_snapshot": {
    "typing_variance_ms": 8,
    "time_to_complete_sec": 2,
    "mouse_move_count": 1,
    "keypress_count": 44
  },
  "ml_anomaly_score": -0.41,
  "flags": ["speed_bot", "email_pattern"]
}
```

---

### GET `/api/users/{user_id}/timeline`
Get full activity timeline for forensic view.

**Response — 200 OK:**
```json
{
  "user_id": "uuid-string",
  "user_email": "user@example.com",
  "timeline": [
    {
      "event_id": "evt-uuid",
      "action": "register",
      "action_type": "register",
      "timestamp": "2025-04-15T10:23:00Z",
      "ip_address": "203.0.113.42",
      "country": "India",
      "user_agent": "Mozilla/5.0 ...",
      "trust_score_at_time": 18,
      "description": "Registration completed; triggered speed_bot, email_pattern",
      "metadata": {
        "triggered_rules": ["speed_bot", "email_pattern"],
        "rule_penalty": 45,
        "behavioral_penalty": 10,
        "ml_penalty": 15
      }
    }
  ]
}
```

---

### PATCH `/api/users/{user_id}/status`
Update user status (approve from quarantine, block, reinstate).

**Request Body:**
```json
{
  "status": "active"
}
```
Valid values: `active`, `quarantined`, `blocked`

**Response — 200 OK:**
```json
{
  "user_id": "uuid-string",
  "status": "active",
  "message": "User status updated"
}
```

---

## 🚨 Alerts Endpoints (Admin Only)

### GET `/api/alerts`
Get recent security alerts. Dashboard polls this every 4 seconds.

**Query Params:**
- `limit` — default 20
- `severity` — filter by `low`, `medium`, `high`, `critical`
- `since` — ISO timestamp, return alerts after this time

**Response — 200 OK:**
```json
{
  "alerts": [
    {
      "alert_id": "alt-uuid",
      "type": "bot_wave",
      "severity": "critical",
      "description": "Rule triggered: platform_velocity_spike for user@example.com",
      "affected_user_ids": ["uuid1", "uuid2"],
      "timestamp": "2025-04-16T09:45:00Z",
      "resolved": false
    },
    {
      "alert_id": "alt-uuid-2",
      "type": "geo_drift",
      "severity": "high",
      "description": "Rule triggered: geo_drift for user@example.com",
      "affected_user_ids": ["uuid-string"],
      "timestamp": "2025-04-16T09:12:00Z",
      "resolved": false
    }
  ]
}
```

Alert types: `bot_wave`, `geo_drift`, `speed_bot`, `email_pattern`, `duplicate_device`, `velocity_spike`, `ml_anomaly`, `captcha_challenge`, `trust_quarantine`

---

### PATCH `/api/alerts/{alert_id}/resolve`
Mark an alert as resolved. The backend ignores the request body and always sets `resolved: true`.

**Response — 200 OK:**
```json
{
  "alert_id": "alt-uuid",
  "resolved": true
}
```

---

## 📊 Analytics Endpoints (Admin Only)

### GET `/api/analytics/velocity`
Registration velocity over time — used for the velocity chart.

**Query Params:**
- `window` — `1h`, `6h`, `24h` (default `1h`)
- `bucket` — `1min`, `5min` (default `1min`)

**Response — 200 OK:**
```json
{
  "window": "1h",
  "data": [
    { "timestamp": "2025-04-16T09:00:00Z", "registrations": 2 },
    { "timestamp": "2025-04-16T09:01:00Z", "registrations": 1 },
    { "timestamp": "2025-04-16T09:02:00Z", "registrations": 14 }
  ],
  "spike_detected": true,
  "spike_at": "2025-04-16T09:02:00Z"
}
```

---

### GET `/api/analytics/trust-distribution`
Trust score distribution for histogram chart.

**Response — 200 OK:**
```json
{
  "bands": [
    { "label": "Safe (80-100)",       "count": 89, "color": "green" },
    { "label": "Caution (60-79)",     "count": 23, "color": "yellow" },
    { "label": "Suspicious (40-59)",  "count": 12, "color": "orange" },
    { "label": "Quarantined (20-39)", "count": 7,  "color": "red" },
    { "label": "Blocked (0-19)",      "count": 3,  "color": "darkred" }
  ],
  "total": 134
}
```

---

### GET `/api/analytics/summary`
Top-level KPI summary for the dashboard header cards.

**Response — 200 OK:**
```json
{
  "total_users": 134,
  "flagged_today": 19,
  "bot_waves_detected": 2,
  "quarantined": 7,
  "blocked": 3,
  "avg_trust_score": 74.3
}
```

---

## 🧠 Internal Scoring Endpoint

### POST `/api/score`
Score a user's behavioral data. Called internally during register/login.
Can also be called directly by Akash's test scripts.

**Requires JWT auth.** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "user_id": "uuid-string",
  "behavioral": {
    "typing_variance_ms": 8,
    "time_to_complete_sec": 1.9,
    "mouse_move_count": 0,
    "keypress_count": 44
  },
  "ip_address": "192.168.1.1",
  "email": "user1@temp.com",
  "user_agent": "python-requests/2.31.0",
  "registrations_from_ip_last_hour": 14,
  "accounts_with_same_ua_today": 0,
  "event_type": "register",
  "registrations_per_minute": 0
}
```

Optional fields for login scoring:
- `current_country` (str)
- `last_country` (str)
- `minutes_since_last_login` (float)

**Response — 200 OK:**
```json
{
  "trust_score": 12,
  "ml_anomaly_score": -0.58,
  "rule_penalty": 45,
  "behavioral_penalty": 10,
  "ml_penalty": 5,
  "triggered_rules": ["speed_bot", "email_pattern", "velocity_exceeded"],
  "recommendation": "quarantine",
  "event_type": "register"
}
```

---

## 🔑 Auth Notes

- All `/api/users/*`, `/api/alerts/*`, `/api/analytics/*`, and `/api/score` routes require `Authorization: Bearer <JWT>` header
- JWT expires in 24 hours (configurable via `JWT_EXPIRE_HOURS`)
- OTP codes expire in 5 minutes
- CAPTCHA tokens expire in 5 minutes
- Trust score thresholds (defined in `scorer.py:get_recommendation`):
  - `>= 70` → direct login (`recommendation: "allow"`)
  - `>= 40` → OTP required (`recommendation: "otp"`)
  - `>= 20` → CAPTCHA challenge (`recommendation: "captcha"`)
  - `< 20` → quarantine, login blocked (`recommendation: "quarantine"`)
- Rate limits: 5 reg/min/IP, 10 login/min/IP, 3 forgot-password/min/IP, 5 reset-password/min/IP

---

*Last updated by: Arindam (Tech Lead)*  
*If you need to change an endpoint shape, update this doc and notify the team in chat before implementing.*
