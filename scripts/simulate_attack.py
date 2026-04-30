"""
SentinelAI -- Live Demo Attack Simulator
Owner: Parthiv

Runs 3 attack scenarios live during the hackathon presentation.
Each scenario triggers visible alerts on the admin dashboard.

Run DURING the demo while the dashboard is projected:
    python simulate_attack.py --scenario all
    python simulate_attack.py --scenario botwave
    python simulate_attack.py --scenario geodrift
    python simulate_attack.py --scenario speedbot
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
import time
import argparse
import random
import string

API_BASE = "http://localhost:8000/api"

# ANSI colors for terminal output during demo
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
DIM     = "\033[2m"


def header(title):
    print(f"\n{BOLD}{CYAN}{'='*55}{RESET}")
    print(f"{BOLD}{CYAN}  [!] SCENARIO: {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*55}{RESET}\n")


def success(msg):
    print(f"  {GREEN}[OK]{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}[WARN]{RESET} {msg}")


def attack(msg):
    print(f"  {RED}[BOT]{RESET} {msg}")


def info(msg):
    print(f"  {DIM}{msg}{RESET}")


# ---------------------------------------------------------
# SCENARIO 1: Bot Wave
# Registers 15 accounts from the same IP in ~8 seconds
# Expected: velocity alert fires, users quarantined
# ---------------------------------------------------------

def scenario_bot_wave():
    header("BOT WAVE -- Mass Registration Attack")
    print(f"  Sending 15 registrations in ~8 seconds from a single IP...")
    print(f"  Watch the dashboard for a bot_wave alert!\n")
    time.sleep(2)

    BOT_IP = "192.168.100.99"  # Same IP for all
    flagged = 0

    for i in range(1, 16):
        email = f"user{i}@temp.com"
        payload = {
            "email": email,
            "password": "password123",
            "behavioral": {
                "typing_variance_ms": random.uniform(2, 8),   # Bot: near zero
                "time_to_complete_sec": random.uniform(0.8, 2.1),
                "mouse_move_count": 0,
                "keypress_count": random.randint(35, 50),
            },
        }

        try:
            resp = requests.post(
                f"{API_BASE}/register",
                json=payload,
                headers={"X-Forwarded-For": BOT_IP, "User-Agent": "python-requests/2.31.0"},
                timeout=3,
            )
            data = resp.json()
            trust = data.get("trust_score", "?")
            status = data.get("status", "?")

            if status == "quarantined":
                attack(f"[{i:02d}/15] {email} -- Trust: {trust} -> QUARANTINED")
                flagged += 1
            else:
                warn(f"[{i:02d}/15] {email} -- Trust: {trust} -> {status}")

        except Exception as e:
            warn(f"[{i:02d}/15] Request failed: {e}")

        time.sleep(0.45)  # 15 requests over ~7 seconds

    print()
    print(f"  {BOLD}Result: {flagged}/15 accounts quarantined{RESET}")
    print(f"  {BOLD}Check dashboard -> Threat Feed for 'bot_wave' alert{RESET}")


# ---------------------------------------------------------
# SCENARIO 2: Geospatial Drift
# Logs in as a seeded user from India, then immediately from Germany
# Expected: geo_drift alert fires
# ---------------------------------------------------------

def scenario_geo_drift(email: str = None, password: str = None):
    header("GEO DRIFT -- Session Hijack Simulation")

    # Use a known seeded user or default demo credentials
    if not email:
        email = "arjun.sharma@gmail.com"
    if not password:
        password = "Demo@abc12345"

    INDIA_IP   = "103.21.58.12"   # India
    GERMANY_IP = "85.208.96.1"    # Germany

    print(f"  Account: {email}")
    print(f"  Step 1: Normal login from India ({INDIA_IP})")
    time.sleep(1.5)

    try:
        resp1 = requests.post(
            f"{API_BASE}/login",
            json={"email": email, "password": password, "ip_address": INDIA_IP,
                  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"},
            timeout=3,
        )
        data1 = resp1.json()
        success(f"Login from India -- Trust: {data1.get('trust_score', '?')}, OTP: {data1.get('otp_required', '?')}")
    except Exception as e:
        warn(f"Login 1 failed: {e}")

    time.sleep(2)
    print(f"\n  Step 2: Login from Germany ({GERMANY_IP}) -- 2 minutes later")
    time.sleep(1.5)

    try:
        resp2 = requests.post(
            f"{API_BASE}/login",
            json={"email": email, "password": password, "ip_address": GERMANY_IP,
                  "user_agent": "python-requests/2.31.0"},
            timeout=3,
        )
        data2 = resp2.json()
        trust = data2.get("trust_score", "?")
        attack(f"Login from Germany -- Trust: {trust} -> GEO DRIFT DETECTED")
    except Exception as e:
        warn(f"Login 2 failed: {e}")

    print()
    print(f"  {BOLD}Check dashboard -> Threat Feed for 'geo_drift' alert{RESET}")


# ---------------------------------------------------------
# SCENARIO 3: Speed Bot
# Completes registration in 1.2 seconds with 0 mouse moves
# Expected: speed_bot + behavioral penalties fire
# ---------------------------------------------------------

def scenario_speed_bot():
    header("SPEED BOT -- Automated Form Submission")
    print(f"  Registering with 1.2s completion time, 0 mouse moves, 3ms typing variance")
    print(f"  A human takes 30-90 seconds. This bot takes 1.2.\n")
    time.sleep(2)

    suffix = "".join(random.choices(string.digits, k=6))
    email = f"speedbot_{suffix}@guerrillamail.com"

    payload = {
        "email": email,
        "password": "password",
        "behavioral": {
            "typing_variance_ms": 3.1,    # Near-zero variance = robot
            "time_to_complete_sec": 1.2,  # Impossible for a human
            "mouse_move_count": 0,        # No mouse at all
            "keypress_count": 44,         # Exact same every time
        },
    }

    try:
        resp = requests.post(
            f"{API_BASE}/register",
            json=payload,
            headers={
                "X-Forwarded-For": "10.0.0.88",
                "User-Agent": "Scrapy/2.11.0 (+https://scrapy.org)",  # Known bot UA
            },
            timeout=3,
        )
        data = resp.json()
        trust = data.get("trust_score", "?")
        status = data.get("status", "?")
        rules = data.get("triggered_rules", [])

        attack(f"Email: {email}")
        attack(f"Trust Score: {trust} -> Status: {status.upper()}")
        attack(f"Rules triggered: {', '.join(rules) if rules else 'none'}")

    except Exception as e:
        warn(f"Request failed: {e}")

    print()
    print(f"  {BOLD}Check dashboard -> User table to see this account flagged{RESET}")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SentinelAI Demo Attack Simulator")
    parser.add_argument(
        "--scenario",
        choices=["all", "botwave", "geodrift", "speedbot"],
        default="all",
        help="Which attack scenario to run (default: all)"
    )
    parser.add_argument("--email", help="Email for geodrift scenario (optional)")
    parser.add_argument("--password", help="Password for geodrift scenario (optional)")
    args = parser.parse_args()

    print(f"\n{BOLD}SentinelAI -- Live Demo Attack Simulator{RESET}")
    print(f"Target API: {API_BASE}")
    print(f"Make sure the backend is running and the dashboard is open!\n")
    input("Press ENTER to begin...\n")

    if args.scenario in ("all", "botwave"):
        scenario_bot_wave()
        if args.scenario == "all":
            print(f"\n  {DIM}Pausing 5 seconds before next scenario...{RESET}")
            time.sleep(5)

    if args.scenario in ("all", "geodrift"):
        scenario_geo_drift(args.email, args.password)
        if args.scenario == "all":
            print(f"\n  {DIM}Pausing 5 seconds before next scenario...{RESET}")
            time.sleep(5)

    if args.scenario in ("all", "speedbot"):
        scenario_speed_bot()

    print(f"\n{BOLD}{GREEN}{'='*55}{RESET}")
    print(f"{BOLD}{GREEN}  Demo complete! All scenarios finished.{RESET}")
    print(f"{BOLD}{GREEN}{'='*55}{RESET}\n")


if __name__ == "__main__":
    main()
