# 📡 SentinelAI — API Contract

> **This document is the source of truth for all endpoints.**  
> Frontend (Debarshi) and Scripts (Parthiv) should build against this contract  
> even before Atul's backend is complete — use mock data in the meantime.

Base URL (local): `http://localhost:8000/api`

---

## 🔐 Authentication Endpoints

### POST `/api/register`
Register a new user. Accepts behavioral payload alongside credentials.

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

**Response — 201 Created:**
```json
{
  "user_id": "uuid-string",
  "trust_score": 82,
  "status": "active",
  "message": "Registration successful"
}
```

**Response — 400 Bad Request (bot detected):**
```json
{
  "user_id": "uuid-string",
  "trust_score": 18,
  "status": "quarantined",
  "message": "Account flagged for review"
}
```

---

### POST `/api/login`
Login endpoint. Returns token or triggers OTP based on trust score.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0 ..."
}
```

**Response — 200 OK (high trust, direct login):**
```json
{
  "token": "eyJhbGci...",
  "trust_score": 85,
  "otp_required": false,
  "user_id": "uuid-string"
}
```

**Response — 200 OK (medium trust, OTP required):**
```json
{
  "token": null,
  "trust_score": 52,
  "otp_required": true,
  "otp_session_id": "temp-session-uuid",
  "user_id": "uuid-string"
}
```

**Response — 403 Forbidden (quarantined):**
```json
{
  "error": "Account suspended pending review",
  "trust_score": 12
}
```

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
  "expires_in_seconds": 300
}
```

---

### POST `/api/otp/verify`
Verify the OTP entered by the user.

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
  "user_id": "uuid-string",
  "message": "Login successful"
}
```

**Response — 400 Bad Request:**
```json
{
  "error": "Invalid or expired OTP"
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
  "timeline": [
    {
      "event_id": "evt-uuid",
      "action": "register",
      "timestamp": "2025-04-15T10:23:00Z",
      "ip_address": "203.0.113.42",
      "country": "India",
      "user_agent": "Mozilla/5.0 ...",
      "trust_score_at_time": 18
    },
    {
      "event_id": "evt-uuid-2",
      "action": "login",
      "timestamp": "2025-04-15T10:25:00Z",
      "ip_address": "85.208.96.1",
      "country": "Germany",
      "user_agent": "Python-requests/2.31",
      "trust_score_at_time": 8
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
      "description": "15 registrations detected in 8 seconds from IP block 192.168.x.x",
      "affected_user_ids": ["uuid1", "uuid2"],
      "timestamp": "2025-04-16T09:45:00Z",
      "resolved": false
    },
    {
      "alert_id": "alt-uuid-2",
      "type": "geo_drift",
      "severity": "high",
      "description": "user@example.com logged in from India then Germany within 47 minutes",
      "affected_user_ids": ["uuid-string"],
      "timestamp": "2025-04-16T09:12:00Z",
      "resolved": false
    }
  ]
}
```

Alert types: `bot_wave`, `geo_drift`, `speed_bot`, `email_pattern`, `duplicate_device`, `velocity_spike`

---

### PATCH `/api/alerts/{alert_id}/resolve`
Mark an alert as resolved.

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
    { "label": "Suspicious (40-59)", "count": 12, "color": "orange" },
    { "label": "Quarantined (20-39)","count": 7,  "color": "red" },
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
  "registrations_from_ip_last_hour": 14
}
```

**Response — 200 OK:**
```json
{
  "trust_score": 12,
  "ml_anomaly_score": -0.58,
  "triggered_rules": ["speed_bot", "email_pattern", "velocity_exceeded"],
  "recommendation": "quarantine"
}
```

---

## 🔑 Auth Notes

- All `/api/admin/*` and analytics routes require `Authorization: Bearer <JWT>` header
- JWT expires in 24 hours
- OTP codes expire in 5 minutes
- Trust score thresholds:
  - `> 70` → direct login, no OTP
  - `40–70` → OTP required
  - `20–40` → OTP + CAPTCHA + admin alert
  - `< 20` → quarantine, login blocked

---

*Last updated by: Arindam (Tech Lead)*  
*If you need to change an endpoint shape, update this doc and notify the team in chat before implementing.*
