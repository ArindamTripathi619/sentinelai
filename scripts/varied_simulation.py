#!/usr/bin/env python3
"""Varied simulation: bot waves, mixed regs, credential stuffing, geodrift, errors."""
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE = "http://localhost:9000/api"
HEADERS = {"Content-Type": "application/json"}

# Helpers

def register(email, password="Test123!", ip=None, ua=None, behavioral=None):
    headers = dict(HEADERS)
    if ip:
        headers["X-Forwarded-For"] = ip
    if ua:
        headers["User-Agent"] = ua
    payload = {"email": email, "password": password}
    if behavioral:
        payload.update({"behavioralData": behavioral})
    try:
        r = requests.post(f"{API_BASE}/register", json=payload, headers=headers, timeout=5)
        return r.status_code, r.json() if r.headers.get('Content-Type','').startswith('application/json') else {}
    except Exception as e:
        return None, {"error": str(e)}


def login(email, password, ip=None, ua=None):
    headers = dict(HEADERS)
    if ip:
        headers["X-Forwarded-For"] = ip
    if ua:
        headers["User-Agent"] = ua
    payload = {"email": email, "password": password}
    try:
        r = requests.post(f"{API_BASE}/login", json=payload, headers=headers, timeout=5)
        return r.status_code, r.json() if r.headers.get('Content-Type','').startswith('application/json') else {}
    except Exception as e:
        return None, {"error": str(e)}


# Simulation waves

def bot_wave(count=60, ip="192.0.2.100", ua="BotUA/1.0"):
    print("\n--- BOT WAVE: starting", count)
    results = []
    def task(i):
        email = f"bot_wave_{int(time.time())}_{i}@temp.com"
        beh = {"typing_variance_ms": 1, "time_to_complete_sec": random.uniform(0.2, 0.8), "mouse_move_count": 0, "keypress_count": 1}
        return register(email, "P@ssw0rd!", ip=ip, ua=ua, behavioral=beh)

    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(task, i) for i in range(count)]
        for f in as_completed(futures):
            results.append(f.result())
    print("BOT WAVE: completed", len(results))
    return results


def mixed_registrations(count=40):
    print("\n--- MIXED REGISTRATIONS: starting", count)
    results = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = []
        for i in range(count):
            # half low-behavior (likely quarantined/flagged), half normal
            if i % 2 == 0:
                email = f"susp_{int(time.time())}_{i}@temp.com"
                behavioral = {"typing_variance_ms": 2, "time_to_complete_sec": random.uniform(0.5, 2.0), "mouse_move_count": 0, "keypress_count": 1}
            else:
                email = f"human_{int(time.time())}_{i}@example.com"
                behavioral = {"typing_variance_ms": random.uniform(60, 200), "time_to_complete_sec": random.uniform(8, 25), "mouse_move_count": random.randint(10,50), "keypress_count": random.randint(60,120)}
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" if i % 3 else "SharedUA/2.0"
            futures.append(ex.submit(register, email, "Test123!", ip=None, ua=ua, behavioral=behavioral))
        for f in as_completed(futures):
            results.append(f.result())
    print("MIXED REGISTRATIONS: completed", len(results))
    return results


def credential_stuffing(victims=6, attempts=30):
    print("\n--- CREDENTIAL STUFFING: preparing victims", victims)
    victims_emails = []
    for i in range(victims):
        email = f"victim_{i}_{int(time.time())}@demo.local"
        # create with a real password
        register(email, "CorrectHorse1!", ip=None, ua="VictimUA/1.0")
        victims_emails.append(email)
    print("Victims created:", victims_emails)

    print("Credential stuffing: starting failed attempts")
    failed = 0
    def attempt(email):
        nonlocal failed
        for _ in range(attempts):
            status, _ = login(email, "WrongPassword!", ip="198.51.100.55")
            if status and status >= 400:
                failed += 1
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(attempt, e) for e in victims_emails]
        for f in as_completed(futures):
            pass
    print("Credential stuffing complete. failed attempts approx:", failed)
    return failed


def geodrift_test():
    print("\n--- GEODRIFT: starting")
    email = f"traveler_{int(time.time())}@demo.local"
    register(email, "Traveller1!", ip="203.0.113.5", ua="TravellerUA/1.0")
    ips = ["202.96.199.50","185.179.39.1","176.28.50.165","49.204.85.50"]
    flagged = 0
    for ip in ips:
        status, _ = login(email, "Traveller1!", ip=ip)
        if status and status >= 400:
            flagged += 1
        time.sleep(0.5)
    print("GEODRIFT complete. flagged logins:", flagged)
    return flagged


def generate_errors(count=20):
    print("\n--- ERROR GENERATION: starting", count)
    # send malformed requests to create 400s and 500s
    errs = 0
    for i in range(count):
        # missing password
        r = requests.post(f"{API_BASE}/register", json={"email": f"bad_{i}@x.com"}, timeout=3)
        if r.status_code >= 400:
            errs += 1
        # invalid endpoint to produce 404
        r2 = requests.get(f"{API_BASE}/nonexistent_endpoint_{i}")
        if r2.status_code >= 400:
            errs += 1
    print("ERROR GENERATION: done; errors produced approx:", errs)
    return errs


def main():
    start = time.time()
    bot_wave(60)
    time.sleep(2)
    mixed_registrations(40)
    time.sleep(2)
    credential_stuffing(8, 24)
    time.sleep(1)
    geodrift_test()
    time.sleep(1)
    generate_errors(30)
    elapsed = time.time() - start
    print('\n--- Simulation complete in %.1f seconds' % elapsed)

if __name__ == '__main__':
    main()
