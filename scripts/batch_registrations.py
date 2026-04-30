"""
Batch registrations script: bots, borderline, benign — prints trust_score and recommendation summary.
Run: python batch_registrations.py
"""

import requests
import random
import time
from collections import defaultdict

API_BASE = "http://127.0.0.1:9000/api"

REALISTIC_IPS = [
    "103.21.58.12", "106.51.71.200", "122.177.94.21", "49.36.80.45",
]

session = requests.Session()


def register(email, password, behavioral, ip):
    try:
        resp = session.post(
            f"{API_BASE}/register",
            json={
                "email": email,
                "password": password,
                "behavioral": behavioral,
            },
            headers={
                "X-Forwarded-For": ip,
                "User-Agent": "BatchTester/1.0",
            },
            timeout=10,
        )
        return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"error": str(e)}


results = defaultdict(list)

# 1) Bot wave: same IP, very bot-like behavior
bot_ip = "203.0.113.10"
for i in range(10):
    email = f"bot_wave_{i}@malicious.test"
    behavioral = {
        "typing_variance_ms": round(random.uniform(0.0, 6.0), 2),
        "time_to_complete_sec": round(random.uniform(0.5, 2.2), 2),
        "mouse_move_count": 0,
        "keypress_count": random.randint(30, 55),
        "session_tempo_sec": 1.0,
        "mouse_entropy_score": 0.05,
        "fill_order_score": 0.1,
    }
    status, data = register(email, "Passw0rd!", behavioral, bot_ip)
    results['bot'].append((status, data))
    print(f"[bot] {i+1}/10 -> {data.get('trust_score', data)}")
    time.sleep(0.12)

# 2) Borderline / semi-automated
for i in range(10):
    email = f"borderline_{i}@suspicious.test"
    behavioral = {
        "typing_variance_ms": round(random.uniform(12, 45), 2),
        "time_to_complete_sec": round(random.uniform(2.5, 7.5), 2),
        "mouse_move_count": random.randint(0, 15),
        "keypress_count": random.randint(35, 75),
        "session_tempo_sec": round(random.uniform(1.5, 4.5), 2),
        "mouse_entropy_score": round(random.uniform(0.15, 0.45), 2),
        "fill_order_score": round(random.uniform(0.2, 0.6), 2),
    }
    ip = random.choice(REALISTIC_IPS)
    status, data = register(email, "Passw0rd!", behavioral, ip)
    results['borderline'].append((status, data))
    print(f"[borderline] {i+1}/10 -> {data.get('trust_score', data)} | rec={data.get('recommendation')}")
    time.sleep(0.18)

# 3) Benign / human-like
for i in range(10):
    email = f"benign_{i}@example.com"
    behavioral = {
        "typing_variance_ms": round(random.uniform(130, 250), 2),
        "time_to_complete_sec": round(random.uniform(20, 90), 2),
        "mouse_move_count": random.randint(30, 140),
        "keypress_count": random.randint(80, 160),
        "session_tempo_sec": round(random.uniform(3, 8), 2),
        "mouse_entropy_score": round(random.uniform(0.6, 0.95), 2),
        "fill_order_score": round(random.uniform(0.8, 1.0), 2),
    }
    ip = random.choice(REALISTIC_IPS)
    status, data = register(email, "Passw0rd!", behavioral, ip)
    results['benign'].append((status, data))
    print(f"[benign] {i+1}/10 -> {data.get('trust_score', data)} | rec={data.get('recommendation')}")
    time.sleep(0.15)

# Summary
print('\nBatch summary:')
for k, entries in results.items():
    scores = [e[1].get('trust_score') for e in entries if isinstance(e[1], dict) and 'trust_score' in e[1]]
    recs = [e[1].get('recommendation') for e in entries if isinstance(e[1], dict)]
    print(f"  {k}: attempts={len(entries)}, succeeded={len(scores)}, avg_trust={sum(scores)/len(scores) if scores else 'N/A'}, recs={dict((r, recs.count(r)) for r in set(recs))}")

# Exit

