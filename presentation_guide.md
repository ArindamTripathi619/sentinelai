Great question — and this is a real demo trap that catches many teams. Here's the full picture:

---

## The Core Problem

You're right on both counts. The system scores trust based on **behavioral signals + IP patterns + email patterns + ML**. If you're a real human typing normally from a legitimate IP with a clean email, the system will correctly give you a high trust score and let you straight in. That's the system working as intended — but it looks boring in a demo.

The fix is **not to fake the system** — it's to **control the inputs** so the system responds correctly to genuinely suspicious signals. There are three clean approaches.

---

## Approach 1 — Pre-Seeded Demo Accounts (Most Reliable)

Before the presentation, seed specific accounts directly into the database with **manually set low trust scores and statuses**. Then log in as those accounts live.

```python
# Run this before the presentation
# scripts/seed_demo_accounts.py

import sqlite3  # or psycopg2 for postgres
import uuid, hashlib

conn = psycopg2.connect("your_connection_string")
cur = conn.cursor()

# Account 1: Will be prompted for OTP (trust score 55)
cur.execute("""
    INSERT INTO users (id, email, password_hash, trust_score, status)
    VALUES (%s, %s, %s, %s, %s)
""", (str(uuid.uuid4()), "demo_otp@cipher.test", 
      hash_password("Demo@1234"), 55, "active"))

# Account 2: Will be quarantined (trust score 15)
cur.execute("""
    INSERT INTO users (id, email, password_hash, trust_score, status)
    VALUES (%s, %s, %s, %s, %s)
""", (str(uuid.uuid4()), "demo_quarantine@cipher.test",
      hash_password("Demo@1234"), 15, "quarantined"))

# Account 3: Will be blocked
cur.execute("""
    INSERT INTO users (id, email, password_hash, trust_score, status)
    VALUES (%s, %s, %s, %s, %s)
""", (str(uuid.uuid4()), "demo_blocked@cipher.test",
      hash_password("Demo@1234"), 5, "blocked"))

conn.commit()
```

Then during the demo you just log in as each account. The login endpoint reads the stored trust score and status — it doesn't re-score on login from scratch. So:

- `demo_otp@cipher.test` → trust score 55 → OTP screen appears
- `demo_quarantine@cipher.test` → status quarantined → blocked with "under review" message
- `demo_blocked@cipher.test` → status blocked → hard block message

**This is the cleanest approach.** Real platforms do exactly this for internal demos — the accounts are pre-configured to represent each state.

---

## Approach 2 — Manipulate Registration Inputs Live (During Demo)

Instead of logging in, **register a new account live** with obviously bot-like inputs. Since your behavioral SDK collects signals from the browser, you can manipulate those signals to score low.

The trick: open your browser's **developer console** and override the behavioral payload before it's sent.

In `behavioral.js`, temporarily add a demo mode override:

```javascript
// Add this to behavioral.js — remove after hackathon
export function setDemoMode(mode) {
  // mode: "bot" | "human" | "normal"
  if (mode === "bot") {
    window.__DEMO_OVERRIDE__ = {
      typing_variance_ms: 3,        // robot-level
      time_to_complete_sec: 1.2,    // impossibly fast
      mouse_move_count: 0,          // no mouse
      keypress_count: 44
    };
  }
}

export function getPayload() {
  if (window.__DEMO_OVERRIDE__) return window.__DEMO_OVERRIDE__;
  // ... normal logic
}
```

Then from the browser console during the demo:

```javascript
// Paste this in console before submitting the registration form
window.__DEMO_OVERRIDE__ = {
  typing_variance_ms: 3,
  time_to_complete_sec: 1.2,
  mouse_move_count: 0,
  keypress_count: 44
}
```

Also register with a disposable email like `user1@temp.com` — that alone triggers the email pattern rule for -20 points. Combined with bot behavioral signals, the trust score will drop low enough to hit quarantine.

**What judges see:** You type into the form normally, but you explain that the hidden payload has been set to simulate a bot. Then you hit submit and the system quarantines the account. Very demonstrable.

---

## Approach 3 — Dedicated Demo Endpoint (Most Professional)

Add a single `/api/demo/score` endpoint that accepts a scenario name and returns what would happen — without actually creating an account. This is purely for the presentation.

```python
# In backend/main.py — demo only, remove in production

@app.post("/api/demo/score")
async def demo_score(scenario: str):
    """
    Demo endpoint for presentation use only.
    Returns what the scoring pipeline would produce for each scenario.
    """
    scenarios = {
        "bot_wave": {
            "email": "user7@temp.com",
            "behavioral": {"typing_variance_ms": 4, "time_to_complete_sec": 1.1,
                          "mouse_move_count": 0, "keypress_count": 42},
            "registrations_from_ip_last_hour": 14,
            "accounts_with_same_ua_today": 6
        },
        "legitimate": {
            "email": "priya.sharma@gmail.com",
            "behavioral": {"typing_variance_ms": 187, "time_to_complete_sec": 43,
                          "mouse_move_count": 62, "keypress_count": 94},
            "registrations_from_ip_last_hour": 1,
            "accounts_with_same_ua_today": 1
        },
        "borderline": {
            "email": "user@outlook.com",
            "behavioral": {"typing_variance_ms": 35, "time_to_complete_sec": 6,
                          "mouse_move_count": 8, "keypress_count": 55},
            "registrations_from_ip_last_hour": 2,
            "accounts_with_same_ua_today": 1
        }
    }
    
    if scenario not in scenarios:
        return {"error": "Unknown scenario"}
    
    data = scenarios[scenario]
    # Run through your actual scoring pipeline
    result = score_registration(**data)
    
    return {
        "scenario": scenario,
        "trust_score": result.trust_score,
        "recommendation": result.recommendation,
        "triggered_rules": result.triggered_rules,
        "rule_penalty": result.rule_penalty,
        "behavioral_penalty": result.behavioral_penalty,
        "ml_penalty": result.ml_penalty
    }
```

During the demo, open Swagger UI (`localhost:9000/docs`) and call this endpoint live. Judges see the real scoring pipeline responding with real numbers for each scenario. It's transparent, honest, and technically impressive.

---

## Recommended Demo Flow for the Presentation

Combine all three approaches for maximum coverage:

**Step 1 — Show a legitimate user (Approach 1)**
Log in as `demo_otp@cipher.test` with password `Demo@1234`.
> *"This is a borderline user with a trust score of 55. Watch what happens."*
→ OTP screen appears. Email arrives. Enter OTP. Login succeeds.
> *"The system applied friction proportional to the risk level. A fully trusted user would have gone straight through."*

**Step 2 — Show a quarantined user (Approach 1)**
Log in as `demo_quarantine@cipher.test`.
> *"This account was flagged during our bot wave simulation. Trust score of 15."*
→ "Account under review" message appears. Can't log in.
> *"They're not banned — they're in Quarantine. The admin can approve or permanently block them."*

**Step 3 — Show a bot registration live (Approach 2)**
Open the registration form. Paste the override in console. Use `user99@temp.com`. Submit.
> *"We've set the behavioral payload to simulate a headless browser — zero mouse movement, 1.2 second completion, 3 millisecond typing variance. Watch the response."*
→ System returns quarantined status with trust score.
> *"The email pattern rule fired, the speed rule fired, the behavioral penalty applied. Total trust score: 12."*

**Step 4 — Show the dashboard reacting (Approach 1 + 2 combined)**
Switch to the admin dashboard tab. Show the new alert in the Live Threat Feed. Click the quarantined user in User Forensics. Open their timeline. Show the metadata JSON with triggered rules.

---

## Regarding Deployed IPs

Your concern about all team IPs being "safe" is only relevant for the **IP velocity rule** — which fires when *the same IP registers multiple accounts in an hour*. One person registering once from their IP will never trigger that. The rules that will always work regardless of IP are:

- Email pattern rule — `user1@temp.com` always fires this
- Speed bot rule — 1.2 second completion always fires this  
- Behavioral penalty — zero mouse moves always fires this
- ML anomaly score — bot-like feature vector always fires this
- Status-based blocks — pre-seeded accounts always work

So even on a deployed version, Approaches 1 and 2 work perfectly. Only the IP velocity scenario needs the attack script, and that's best shown via `simulate_attack.py` running in a terminal anyway — not through manual browser interaction.

The bottom line: **never rely on live manual typing to demonstrate security features**. Always control the inputs. Pre-seeded accounts for state demonstration, console override for registration demo, Swagger for pipeline transparency. That combination covers every scenario a judge might ask for.