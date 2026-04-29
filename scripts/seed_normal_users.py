"""
SentinelAI — Normal User Seeder
Owner: Parthiv

Registers 50 realistic users via the API to pre-populate the dashboard.
Run this BEFORE the demo to have a healthy baseline of users.

Run: python seed_normal_users.py
"""

import requests
import random
import time
import string
from datetime import datetime

API_BASE = "http://localhost:8000/api"

FIRST_NAMES = [
    "Arjun", "Priya", "Rahul", "Sneha", "Vikram", "Ananya", "Rohan", "Kavya",
    "Aditya", "Pooja", "Kiran", "Meera", "Sanjay", "Divya", "Amit", "Nisha",
    "Raj", "Swati", "Nikhil", "Riya", "Shiv", "Tanvi", "Harsh", "Simran",
    "Dev", "Ishaan", "Sakshi", "Aryan", "Rhea", "Kabir"
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Mehta", "Shah", "Joshi",
    "Nair", "Iyer", "Reddy", "Rao", "Das", "Bose", "Ghosh", "Chatterjee"
]

DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "kiit.ac.in", "kiitstudent.in", "protonmail.com"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/121.0 Firefox/121.0",
]

REALISTIC_IPS = [
    "103.21.58.12", "106.51.71.200", "122.177.94.21", "49.36.80.45",
    "103.245.96.22", "115.240.98.1", "59.144.68.200", "182.73.100.3",
    "27.7.90.1", "117.200.45.80", "45.118.144.200", "14.142.107.112",
]


def random_email(first, last):
    suffix = random.choice(["", str(random.randint(1, 99)), "_" + str(random.randint(1990, 2004))])
    separator = random.choice([".", "_", ""])
    local = f"{first.lower()}{separator}{last.lower()}{suffix}"
    domain = random.choice(DOMAINS)
    return f"{local}@{domain}"


def human_behavioral():
    """Generate realistic human behavioral signals."""
    return {
        "typing_variance_ms": round(random.gauss(180, 55), 1),
        "time_to_complete_sec": round(random.gauss(48, 18), 1),
        "mouse_move_count": random.randint(20, 120),
        "keypress_count": random.randint(60, 160),
    }


def register_user(email, password, behavioral, ip):
    try:
        resp = requests.post(
            f"{API_BASE}/register",
            json={
                "email": email,
                "password": password,
                "behavioral": behavioral,
            },
            headers={
                "X-Forwarded-For": ip,
                "User-Agent": random.choice(USER_AGENTS),
            },
            timeout=5,
        )
        return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"error": str(e)}


def main():
    print("=" * 55)
    print("  SentinelAI — Seeding Normal Users")
    print(f"  Target: {API_BASE}")
    print("=" * 55)

    success = 0
    failed = 0

    for i in range(50):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email = random_email(first, last)
        password = "Demo@" + "".join(random.choices(string.ascii_letters + string.digits, k=8))
        behavioral = human_behavioral()
        ip = random.choice(REALISTIC_IPS)

        status, resp = register_user(email, password, behavioral, ip)

        if status == 201:
            trust = resp.get("trust_score", "?")
            print(f"  ✅ [{i+1:02d}/50] {email} — Trust: {trust}")
            success += 1
        else:
            print(f"  ❌ [{i+1:02d}/50] {email} — Failed: {resp}")
            failed += 1

        # Randomized delay — simulate users registering over time
        time.sleep(random.uniform(0.3, 1.2))

    print("\n" + "=" * 55)
    print(f"  Done: {success} succeeded, {failed} failed")
    print(f"  Dashboard should now show {success} normal users.")
    print("=" * 55)


if __name__ == "__main__":
    main()
