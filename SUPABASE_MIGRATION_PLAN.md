# 🚀 SentinelAI → Supabase Migration Plan

> **Current State:** SQLite + Custom JWT + Custom OTP email
> **Target State:** Supabase PostgreSQL + Supabase Auth + Supabase Email

---

## 📊 Executive Summary

| Aspect | Current | Supabase | Benefit |
|---|---|---|---|
| **Database** | SQLite (/tmp - ephemeral) | PostgreSQL (managed) | Persistent, scalable, multi-instance |
| **Auth** | Custom JWT + bcrypt | Supabase Auth | Built-in session mgmt, faster |
| **OTP Email** | Gmail SMTP (custom) | Supabase Auth templates | Automatic, reliable, branded |
| **Password Hash** | bcrypt (manual) | Handled by Supabase | No custom code needed |
| **API Routes** | Custom /api/register, /api/login | Supabase Auth endpoints | Less backend code |
| **Session** | localStorage JWT | Supabase session token | Same security model |
| **Scoring** | Backend logic ✅ | Still custom ✅ | Unchanged |

## 🔐 Current Supabase Project

Use the provided Supabase project as the target migration environment:

- Project URL: `https://yevnlrajklfkqjhcrdps.supabase.co`
- Frontend publishable key: map it to `VITE_SUPABASE_ANON_KEY`
- Backend secret key: map it to `SUPABASE_SERVICE_ROLE_KEY`

Rules:

- Never expose the secret key in the browser.
- Use the publishable key only in frontend code.
- Keep the service role key server-side for admin writes, migrations, and privileged reads.

---

## 🎯 What Moves to Supabase

### ✅ Move completely to Supabase-managed services

| Capability | Current implementation | Supabase target | Notes |
|---|---|---|---|
| **Identity and password storage** | `backend/auth.py` bcrypt + JWT | `auth.users` | Supabase stores passwords and issues sessions |
| **Email verification / password reset / OTP mail** | Gmail SMTP + `otp_sessions` | Supabase Auth email templates | Use built-in email flows instead of custom SMTP |
| **Session issuance** | Custom JWT signing | Supabase Auth session JWT | Frontend can keep the session automatically |
| **Admin user lifecycle** | Manual DB updates | Supabase Auth admin actions | Create, ban, reset, and invite from server-side code |

### ⚠️ Move to Supabase Postgres, but keep app-owned tables

| Table | Current | Target | Change |
|---|---|---|---|
| **users** | SQLite SQLAlchemy model | `public.profiles` or `public.users` linked to `auth.users.id` | Remove `password_hash`; keep trust, status, behavioral snapshot, last login/IP |
| **events** | SQLite table | `public.events` | Same shape, better indexes and JSONB for metadata |
| **alerts** | SQLite table | `public.alerts` | Same shape, JSONB for affected users |

### ❌ Remove after migration

| Artifact | Why it goes away |
|---|---|
| **`otp_sessions` table** | Supabase Auth handles OTP/email verification and session issuance |
| **Custom password hashing** | Supabase Auth owns password hashing and verification |
| **Custom JWT minting** | Supabase Auth already returns access and refresh tokens |

### Optional Supabase services to consider later

| Service | Good fit for SentinelAI | Recommendation |
|---|---|---|
| **Realtime** | Live threat feed / alert stream in the dashboard | Strong candidate once core auth/data migration is stable |
| **Edge Functions** | Webhook processing, scheduled notifications, export jobs | Optional; not required for the first migration pass |
| **Storage** | Evidence uploads, screenshots, attachments, forensic artifacts | Only if the product starts storing files |
| **Cron** | Daily cleanup, anomaly rollups, digest emails | Useful for automated maintenance |

---

## 📋 Detailed Migration Breakdown

### 1️⃣ Database Tables (SQLAlchemy → Supabase PostgreSQL)

#### **Current Schema → Supabase Schema**

```sql
-- CURRENT (SQLAlchemy/SQLite)
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  ❌ REMOVE (Supabase Auth handles this)
    trust_score INTEGER DEFAULT 100,
    status TEXT DEFAULT 'active',
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    last_ip TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    typing_variance_ms FLOAT,
    time_to_complete_sec FLOAT,
    mouse_move_count INTEGER,
    keypress_count INTEGER,
    ml_anomaly_score FLOAT,
    triggered_flags TEXT
);

CREATE TABLE otp_sessions (  ❌ DELETE ENTIRE TABLE
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    delivery_status TEXT,
    delivery_attempts INTEGER,
    last_delivery_error TEXT
);

-- NEW (Supabase PostgreSQL)
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,  -- Denormalized from auth.users, sync via trigger
    trust_score INTEGER DEFAULT 100,
    status TEXT DEFAULT 'active',  -- active | quarantined | blocked
    registered_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,
    last_ip TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Behavioral snapshot
    typing_variance_ms FLOAT,
    time_to_complete_sec FLOAT,
    mouse_move_count INTEGER,
    keypress_count INTEGER,
    
    -- ML output
    ml_anomaly_score FLOAT,
    triggered_flags JSONB  -- Changed from TEXT to JSONB for better querying
);

CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    ip_address TEXT,
    country TEXT,
    user_agent TEXT,
    trust_score_at_time INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    affected_user_ids JSONB,  -- Changed from TEXT to JSONB
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- OTP SESSIONS TABLE - REMOVED
-- Supabase Auth handles OTP natively, no need for separate table
```

---

### 2️⃣ Authentication (Custom JWT → Supabase Auth)

#### **Current Flow**
```
User submits (email, password)
    ↓
Backend: hash_password() with bcrypt
    ↓
Backend: verify_password() at login
    ↓
Backend: create_access_token() (JWT with SECRET_KEY)
    ↓
Frontend: store token in localStorage
    ↓
Frontend: attach "Authorization: Bearer <token>" to requests
```

#### **New Flow (Supabase Auth)**
```
User submits (email, password)
    ↓
Frontend: supabase.auth.signUp() or supabase.auth.signInWithPassword()
    ↓
Supabase Auth: handles password hashing (bcrypt), returns session
    ↓
Frontend: Supabase client stores session automatically (localStorage)
    ↓
Frontend: All requests automatically include Authorization header
    ↓
Backend: Extract user from "Authorization: Bearer <supabase_token>"
```

#### **Important correction for this app**

Supabase gives you two auth patterns, and the migration plan should choose one explicitly:

1. **Email + password** with optional email confirmation. This is closest to the current app.
2. **Passwordless email OTP / magic link**. Use this only if you want to remove passwords entirely.

For SentinelAI, the best migration path is **email + password plus optional verification email** so the current UX remains familiar while the storage and token handling move to Supabase.

#### **Code Changes Required**

**Remove from `backend/auth.py`:**
- `hash_password()` function — Supabase handles this
- `verify_password()` function — Supabase handles this
- `create_access_token()` function — Supabase returns JWT
- Custom JWT verification in `get_current_user()` — Use Supabase JWT verification

**Keep in `backend/auth.py`:**
- `@router.post("/register")` — compatibility wrapper during transition, or remove once the frontend calls Supabase directly
- `@router.post("/login")` — same idea; can be a compatibility wrapper
- `@router.post("/otp/send")` and `@router.post("/otp/verify")` — only if you keep a custom OTP flow; otherwise delete them and use Supabase Auth flows
- Scoring and alert logic — **Unchanged**

---

### 3️⃣ OTP Email (Gmail SMTP → Supabase Auth Email)

#### **Current Flow**
```
Backend: generate random 6-digit OTP
    ↓
Backend: save to otp_sessions table with 5-min expiry
    ↓
Backend: send via Gmail SMTP (requires SMTP credentials)
    ↓
User: receives email, enters OTP manually
    ↓
Backend: verify OTP code against otp_sessions table
```

#### **New Flow (Supabase Auth)**
```
Supabase Auth: generates OTP automatically
    ↓
Supabase Auth: sends email via Resend.com (default) or your SMTP
    ↓
User: receives identical email, enters OTP
    ↓
Supabase Auth: verifies OTP, returns session
```

**Advantages:**
- OTP template is customizable
- Resend is faster/more reliable than Gmail SMTP
- No need to manage `otp_sessions` table
- No retry logic needed
- Email is batched and rate-limited by Supabase

---

### 4️⃣ Frontend (localStorage JWT → Supabase Session)

#### **Current Code** (`frontend/src/lib/api.js`)
```javascript
// Manual JWT handling
export function getAuthToken() {
  return localStorage.getItem('sentinelai_token')
}

export function setAuthToken(token) {
  localStorage.setItem('sentinelai_token', token)
}

api.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

#### **New Code** (Supabase Client)
```javascript
// Supabase handles session automatically
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

// All auth calls go through Supabase
export async function register(email, password) {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

export async function login(email, password) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

// For app-owned backend endpoints, read the session token from Supabase
// and forward it as Bearer auth to FastAPI.
const { data } = await supabase
  .from('users')
  .select('*')
  .eq('id', userId)
```

#### **Frontend migration choice**

You have two viable patterns:

1. **Preferred:** frontend talks directly to Supabase Auth for sign-up/sign-in, then talks to FastAPI for scoring and dashboards.
2. **Compatibility mode:** frontend keeps hitting `/api/register` and `/api/login`, while those routes become thin wrappers around Supabase Auth.

The preferred pattern is cleaner and removes the most backend auth code.

---

### 5️⃣ Backend API Routes (Partially Deprecated)

#### **Routes That Change**

| Endpoint | Current | New | Action |
|---|---|---|---|
| `POST /api/register` | Custom bcrypt + JWT | Call Supabase Auth | Simplify significantly |
| `POST /api/login` | Verify password + JWT | Call Supabase Auth | Simplify significantly |
| `POST /api/otp/send` | Generate + send via SMTP | Call Supabase Auth | Remove (Auth handles) |
| `POST /api/otp/verify` | Check otp_sessions table | Call Supabase Auth | Remove (Auth handles) |

#### **Routes that should probably stay in FastAPI**

| Endpoint family | Why keep it in FastAPI |
|---|---|
| `POST /api/score` | Your behavioral, rules, and ML scoring is custom business logic |
| `GET /api/users*` | The dashboard needs app-specific projections, filters, and timeline formatting |
| `GET /api/alerts*` | Alerts are app-specific security records, not raw auth data |
| `GET /api/analytics/*` | Dashboard aggregations are easier to control in app code |

Supabase can still back these endpoints with Postgres, but FastAPI remains the orchestration layer.

## 🧱 Database Schema Review

### Current models from the codebase

- `User` in `backend/models.py`
- `Event` in `backend/models.py`
- `Alert` in `backend/models.py`
- `OtpSession` in `backend/models.py`

### Recommended Supabase schema

#### `auth.users`

Managed by Supabase. Do not create your own password columns in app tables.

#### `public.profiles` or `public.users`

Recommended columns:

- `id uuid primary key references auth.users(id) on delete cascade`
- `email text not null`
- `trust_score integer default 100`
- `status text default 'active'`
- `registered_at timestamptz default now()`
- `last_login_at timestamptz`
- `last_ip text`
- `is_admin boolean default false`
- `typing_variance_ms double precision`
- `time_to_complete_sec double precision`
- `mouse_move_count integer`
- `keypress_count integer`
- `ml_anomaly_score double precision`
- `triggered_flags jsonb default '[]'::jsonb`

#### `public.events`

Recommended columns:

- `id uuid primary key default gen_random_uuid()`
- `user_id uuid references public.users(id) on delete cascade`
- `action text not null`
- `ip_address text`
- `country text`
- `user_agent text`
- `trust_score_at_time integer`
- `created_at timestamptz default now()`
- `metadata jsonb default '{}'::jsonb`

#### `public.alerts`

Recommended columns:

- `id uuid primary key default gen_random_uuid()`
- `type text not null`
- `severity text not null`
- `description text`
- `affected_user_ids jsonb default '[]'::jsonb`
- `resolved boolean default false`
- `created_at timestamptz default now()`

### RLS and access model

- Enable RLS on every exposed `public` table.
- `profiles`: authenticated users can read/update their own row; admins can read all.
- `events` and `alerts`: backend service role writes; dashboard reads should be admin-only.
- Do not rely on `user_metadata` for authorization decisions; keep admin flags in app metadata or the profile table.

### Supabase API exposure note

As of the recent Supabase change, new public tables are not automatically exposed to the Data API. If the frontend will query tables directly through `supabase-js`, explicitly expose those tables and grant the right roles. If FastAPI talks directly to Postgres, this is less important for the app path, but RLS still matters.

### Concrete schema file

Use [supabase/schema.sql](supabase/schema.sql) as the base schema for the project. It creates:

- `public.users`
- `public.events`
- `public.alerts`
- the `auth.users` profile sync trigger
- RLS policies and the minimal grants needed for authenticated reads

#### **Routes That Stay (Mostly Unchanged)**

| Endpoint | Status | Change |
|---|---|---|
| `POST /api/score` | ✅ Unchanged | Same scoring logic |
| `GET /api/users` | ✅ Mostly unchanged | Read from Supabase instead of SQLite |
| `GET /api/users/{id}` | ✅ Mostly unchanged | Same |
| `GET /api/users/{id}/timeline` | ✅ Mostly unchanged | Same |
| `PATCH /api/users/{id}/status` | ✅ Mostly unchanged | Same |
| `GET /api/alerts` | ✅ Unchanged | Same |
| `GET /api/analytics/*` | ✅ Unchanged | Same |

---

## 🔧 Implementation Plan (Phase-by-Phase)

### **Phase 1: Supabase Setup (1 hour)**

1. Create Supabase account at https://supabase.com (free tier, no CC needed)
2. Create new project (e.g., "SentinelAI")
3. Save credentials:
   - Project URL: `https://xxx.supabase.co`
   - Anon Key: `eyJhbGciOiJIUzI1NiIs...`
   - Service Role Key: (for backend auth)
4. Create PostgreSQL tables from SQL above
5. Enable Email Auth (Auth > Email Templates)
6. Turn on RLS and add policies before the frontend starts reading tables directly

**Deliverable:** `.env.local` with Supabase credentials

---

### **Phase 2: Frontend (Supabase Auth) (2–3 hours)**

**File: `frontend/src/lib/supabase.js` (NEW)**
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)

export default supabase

// Helper functions
export async function register(email, password) {
  return supabase.auth.signUp({ email, password })
}

export async function login(email, password) {
  return supabase.auth.signInWithPassword({ email, password })
}

export async function logout() {
  return supabase.auth.signOut()
}

export async function getCurrentUser() {
  const { data } = await supabase.auth.getUser()
  return data.user
}

export async function getSession() {
  const { data } = await supabase.auth.getSession()
  return data.session
}
```

**File: `frontend/src/auth/Login.jsx` (MODIFY)**
- Replace axios calls to `/api/login`
- Use `supabase.auth.signInWithPassword()`
- Supabase handles the session lifecycle automatically
- Keep the dashboard redirect logic after successful session creation

**File: `frontend/src/auth/Register.jsx` (MODIFY)**
- Replace axios calls to `/api/register`
- Use `supabase.auth.signUp()`
- Handle email confirmation flow if enabled in Supabase Auth settings

**File: `frontend/src/lib/api.js` (MODIFY)**
```javascript
import supabase from './supabase'

// Get token from Supabase session (automatic)
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data?.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

**Deliverable:** Frontend auth fully uses Supabase, all tokens from Supabase

---

### **Phase 3: Backend (Supabase JWT Verification) (2 hours)**

**File: `backend/supabase_client.py` (NEW)**
```python
import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_token(token: str):
    """Verify Supabase JWT token and return user."""
    try:
    response = supabase.auth.get_user(token)
    return response.user
    except Exception as e:
        return None
```

**File: `backend/auth.py` (MAJOR REFACTOR)**

Remove:
- `hash_password()` — Done by Supabase
- `verify_password()` — Done by Supabase
- `create_access_token()` — Done by Supabase
- Custom JWT logic

Simplify:
```python
from fastapi import Depends, HTTPException
from supabase_client import supabase, verify_token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Verify Supabase JWT and return user."""
    auth_user = await verify_token(token)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user profile from public.users
    user = supabase.table('users').select('*').eq('id', auth_user.id).single().execute()
    return user.data

@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    behavioral = data.get("behavioral", {})
    
    # Call Supabase Auth (don't hash locally)
    auth_response = supabase.auth.sign_up({
        "email": email,
        "password": password,
    })
    
    if auth_response.user:
        # Create extended profile in public.users
        user_id = auth_response.user.id
        trust_score = scoring_logic(behavioral, ...)  # Your logic
        
        supabase.table('users').insert({
            'id': user_id,
            'email': email,
            'trust_score': trust_score,
            'status': 'active' if trust_score >= 40 else 'quarantined',
            'typing_variance_ms': behavioral.get('typing_variance_ms'),
            'time_to_complete_sec': behavioral.get('time_to_complete_sec'),
            'mouse_move_count': behavioral.get('mouse_move_count'),
            'keypress_count': behavioral.get('keypress_count'),
        }).execute()
        
        return {"user_id": user_id, "trust_score": trust_score}
    else:
        raise HTTPException(status_code=400, detail="Registration failed")

@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    # Supabase Auth handles password verification
    auth_response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })
    
    if auth_response.user and auth_response.session:
        user_id = auth_response.user.id
        # ... scoring and alert logic ...
        return {
            "token": auth_response.session.access_token,
            "user_id": user_id,
            "trust_score": trust_score,
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Key Change:**
- Backend no longer verifies passwords
- Backend calls Supabase Auth for credential checking
- Backend reads user from Supabase PostgreSQL
- Scoring logic stays intact

**Deliverable:** Backend trusts Supabase for auth, uses Supabase JWT tokens

---

### **Phase 4: Database Migration (1–2 hours)**

**Step 1: Export SQLite data**
```bash
sqlite3 sentinel.db ".dump" > sentinel_dump.sql
```

**Step 2: Transform schema**
- Convert timestamps: `DATETIME` → `TIMESTAMP`
- Convert UUID: `TEXT` → `UUID`
- Remove `password_hash` column (not needed in public.users)

**Step 3: Import to Supabase**
```bash
psql $SUPABASE_CONNECTION_STRING < schema.sql
psql $SUPABASE_CONNECTION_STRING < data.sql
```

**Step 4: Delete otp_sessions table**
- No longer needed

**Deliverable:** SQLite data migrated to Supabase PostgreSQL

---

### **Phase 5: Testing & Validation (1–2 hours)**

1. ✅ Register new user → Check `auth.users` + `public.users`
2. ✅ Login → Check JWT from Supabase
3. ✅ OTP send → Email arrives
4. ✅ OTP verify → Session created
5. ✅ Dashboard access → GET /api/users works
6. ✅ Behavioral scoring → POST /api/score works
7. ✅ Alerts creation → Events logged to Supabase
8. ✅ Admin routes → All analytics work

**Deliverable:** All core features verified on Supabase

---

### **Phase 6: Deployment (30 min)**

1. Update `vercel.json`:
   ```json
   "env": {
     "SUPABASE_URL": "@supabase_url",
     "SUPABASE_SERVICE_ROLE_KEY": "@supabase_key"
   }
   ```

2. Deploy with Supabase credentials:
   ```bash
   vercel deploy --prod --env SUPABASE_URL=... --env SUPABASE_SERVICE_ROLE_KEY=...
   ```

3. Verify in production

**Deliverable:** Full production deployment with Supabase

---

## 📝 Files to Modify

| File | Action | Complexity |
|---|---|---|
| `frontend/src/lib/supabase.js` | CREATE | Low (new file) |
| `frontend/src/auth/Login.jsx` | MODIFY | Medium |
| `frontend/src/auth/Register.jsx` | MODIFY | Medium |
| `frontend/src/lib/api.js` | MODIFY | Low |
| `backend/supabase_client.py` | CREATE | Low (new file) |
| `backend/auth.py` | REFACTOR | High (remove auth logic) |
| `backend/database.py` | REPLACE | Point SQLAlchemy at Supabase Postgres, not SQLite |
| `backend/models.py` | REWORK | Keep ORM models, but align with Postgres and JSONB |
| `backend/mailer.py` | DEPRECATE | Keep only if you retain a fallback SMTP path |
| `requirements.txt` | MODIFY | Add Supabase client libs if backend uses them; remove only unused packages |
| `vercel.json` | MODIFY | Add Supabase env vars |

---

## 🎁 What You Gain

| Feature | Before | After |
|---|---|---|
| **Database persistence** | /tmp (ephemeral) ❌ | PostgreSQL (durable) ✅ |
| **Multi-instance support** | In-memory sessions ❌ | Supabase sessions ✅ |
| **Automatic email delivery** | Custom SMTP retry logic | Supabase Resend integration ✅ |
| **User enumeration protection** | Manual (hard to verify) | Built-in (Supabase) ✅ |
| **OTP expiry management** | Custom logic + table | Automatic ✅ |
| **Backend code** | 1000+ lines of auth | ~200 lines (just calls Supabase) |
| **Email config** | Requires Gmail app password | Zero secrets needed |
| **Rate limiting** | In-memory slowapi | Can use Supabase edge functions |
| **RLS policies** | Manual checks ✅ | Supabase RLS rules |

---

## ⚠️ What Stays the Same

✅ **No changes needed to:**
- `backend/scorer.py` — Trust score logic unchanged
- `backend/rules.py` — Rules engine unchanged
- `backend/ml_model.py` — ML model unchanged
- `backend/geo.py` — Geolocation unchanged
- `backend/users.py` — User endpoints mostly unchanged
- `backend/alerts.py` — Alert creation mostly unchanged
- `backend/analytics.py` — Analytics endpoints unchanged
- `frontend/src/dashboard/*` — Dashboard unchanged
- `frontend/src/sdk/behavioral.js` — Behavioral SDK unchanged
- API contracts in `API.md` — Endpoints stay same

### What should not move to Supabase in the first pass

- Behavioral SDK collection in the browser
- The scoring engine in `backend/scorer.py`
- The rule engine in `backend/rules.py`
- Geolocation lookups in `backend/geo.py`
- Dashboard composition and charts in the React app
- Synthetic demo scripts in `scripts/`

These are app-specific and are better kept in the existing codebase.

---

## 🧭 Concrete Migration Order

1. Create the Supabase tables by running [supabase/schema.sql](supabase/schema.sql) in the SQL editor.
2. Configure Supabase Auth for email + password, and keep email confirmation enabled only if you want verification before first login.
3. Set these environment variables in Vercel and local dev:
  - `VITE_SUPABASE_URL`
  - `VITE_SUPABASE_ANON_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
4. Update the backend to use Supabase Postgres instead of SQLite for `users`, `events`, and `alerts`.
5. Remove custom OTP/session creation logic once Supabase Auth is handling sign-up and sign-in.
6. Update the frontend auth pages to call Supabase Auth directly, or keep the current backend routes temporarily as wrappers.
7. Verify the full path:
  - sign up
  - confirm email if enabled
  - sign in
  - create a user profile row
  - read the dashboard
  - write an alert/event
8. Only after validation, retire the SQLite fallback and the Gmail SMTP path.

---

## 🚀 Migration Timeline

| Phase | Duration | Start | End |
|---|---|---|---|
| P1: Supabase Setup | 1 hour | Day 1 morning | 11 AM |
| P2: Frontend Auth | 2–3 hours | Day 1 11 AM | 2 PM |
| P3: Backend JWT | 2 hours | Day 1 2 PM | 4 PM |
| P4: Data Migration | 1–2 hours | Day 1 4 PM | 5:30 PM |
| P5: Testing | 1–2 hours | Day 1 5:30 PM | 7 PM |
| P6: Deploy | 30 min | Day 2 morning | 9:30 AM |
| **TOTAL** | **~8–9 hours** | | |

---

## ✅ Success Criteria

- [ ] Supabase project created, tables migrated
- [ ] Frontend registers → Supabase Auth user created
- [ ] Frontend login → Supabase JWT returned
- [ ] OTP email arrives (auto-sent by Supabase)
- [ ] OTP verified → Session persists
- [ ] Dashboard access works
- [ ] No logout on page refresh
- [ ] Trust scores calculated correctly
- [ ] Events logged to Supabase
- [ ] Alerts appear on dashboard
- [ ] Admin routes work
- [ ] Production deployment stable

---

## 💡 Pro Tips

1. **Keep local SQLite for dev:**
   ```bash
   # Dev: use local SQLite
   DATABASE_TYPE=sqlite python main.py
   
   # Prod: use Supabase
   export SUPABASE_URL=...
   python main.py
   ```

2. **Use Supabase CLI for local development:**
   ```bash
   npm install -g supabase
   supabase start  # Local Postgres + Auth
   ```

3. **Test OTP flow locally:**
   - Supabase local dev emulates email (logs to console)
   - No need for Gmail credentials in dev

4. **Backup data before migration:**
   ```bash
   sqlite3 sentinel.db ".dump" > backup.sql
   ```

---

*This is your north star for migration. Print it, follow it step-by-step, and you'll have a bulletproof production setup.*

