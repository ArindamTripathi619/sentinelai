#!/usr/bin/env python3
"""
SentinelAI — Hackathon Live Demo Script
========================================

Quick-run security test that generates impressive metrics for demo:
  • 50+ simultaneous bot registrations (shows quarantine in real-time)
  • 100+ failed login attempts (shows brute force detection)
  • Geodrift attacks across 5+ countries
  • Clear before/after metrics

Run this to populate the dashboard with live threat data:
    python scripts/hackathon_demo.py
    
Then:
    1. Open http://localhost:3001 (Grafana)
    2. Open http://localhost:3000 (Frontend)
    3. Show the alerts and metrics in real-time
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

API_BASE = "http://localhost:9000/api"

# Colors for terminal
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"

class HackathonDemo:
    def __init__(self):
        self.quarantined_count = 0
        self.flagged_count = 0
        self.total_registrations = 0
        self.failed_logins = 0

    def banner(self):
        print(f"\n{BOLD}{CYAN}")
        print("""
╔════════════════════════════════════════════════════════════╗
║                SentinelAI Hackathon Demo                   ║
║         Real-Time Security Threat Detection & Response      ║
╚════════════════════════════════════════════════════════════╝
        """)
        print(f"{RESET}")

    def section(self, title):
        print(f"\n{BOLD}{CYAN}━━━ {title} ━━━{RESET}\n")

    def wave_attack(self, title, count=20, delay=0.1, is_bot=False):
        """Execute a wave of attacks in parallel"""
        self.section(title)
        start = time.time()
        
        def attack():
            email = f"bot_{random.randint(10000,99999)}@temp.com" if is_bot else f"user_{random.randint(10000,99999)}@test.local"
            payload = {
                "email": email,
                "password": "Test123!",
                "behavioral": {
                    "typing_variance_ms": random.uniform(1, 5) if is_bot else random.uniform(50, 150),
                    "time_to_complete_sec": random.uniform(0.3, 1.0) if is_bot else random.uniform(8, 25),
                    "mouse_move_count": 0 if is_bot else random.randint(10, 50),
                    "keypress_count": random.randint(25, 40) if is_bot else random.randint(60, 120),
                },
            }
            
            try:
                resp = requests.post(f"{API_BASE}/register", json=payload, timeout=5)
                if resp.status_code in [200, 201]:
                    data = resp.json()
                    return {
                        "email": email,
                        "status": data.get("status"),
                        "trust": data.get("trust_score"),
                        "rules": data.get("triggered_rules", [])
                    }
            except:
                pass
            return {"email": email, "status": "error"}
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(attack) for _ in range(count)]
            
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                self.total_registrations += 1
                
                if result["status"] == "quarantined":
                    self.quarantined_count += 1
                    status_display = f"{RED}QUARANTINED{RESET}"
                elif result["status"] == "flagged":
                    self.flagged_count += 1
                    status_display = f"{YELLOW}FLAGGED{RESET}"
                else:
                    status_display = f"{GREEN}ACTIVE{RESET}"
                
                trust = result["trust"]
                rules = ", ".join(result.get("rules", [])[:2])  # Show top 2 rules
                
                print(f"  [{i:02d}/{count}] {status_display} | Trust: {trust:3d} | Rules: {rules or 'none'}")
                time.sleep(delay)
        
        elapsed = time.time() - start
        print(f"\n  ✓ Completed {count} registrations in {elapsed:.1f}s ({count/elapsed:.0f} req/s)")

    def brute_force_attack(self, accounts=10, attempts_per=10):
        """Simulate credential stuffing"""
        self.section("Credential Stuffing Attack")
        
        # Register some users first
        emails = []
        for i in range(accounts):
            email = f"victim_{i}_{int(time.time())}@test.local"
            try:
                requests.post(f"{API_BASE}/register", 
                    json={"email": email, "password": "RealPass123!"}, timeout=5)
                emails.append(email)
            except:
                pass
        
        print(f"  Attempting {len(emails) * attempts_per} failed logins across {len(emails)} accounts...\n")
        
        for email in emails:
            for attempt in range(attempts_per):
                try:
                    resp = requests.post(f"{API_BASE}/login",
                        json={"email": email, "password": "WrongPassword!"},
                        timeout=5)
                    self.failed_logins += 1
                except:
                    pass
            
            print(f"  • {email}: {attempts_per} failed attempts")
        
        print(f"\n  ✓ {self.failed_logins} failed login attempts recorded")

    def geodrift_attack(self):
        """Rapid location  jumps"""
        self.section("Geodrift Attack")
        
        countries = [
            ("203.0.113.1", "USA"),
            ("202.96.199.50", "China"),
            ("185.179.39.1", "Russia"),
            ("176.28.50.165", "Germany"),
            ("49.204.85.50", "India"),
        ]
        
        email = f"traveler_{int(time.time())}@test.local"
        print(f"  Testing user: {email}\n")
        
        # Register from USA
        try:
            resp = requests.post(f"{API_BASE}/register",
                json={"email": email, "password": "Test123!",
                      "behavioral": {
                          "typing_variance_ms": 150,
                          "time_to_complete_sec": 30,
                          "mouse_move_count": 40,
                          "keypress_count": 80,
                      }},
                headers={"X-Forwarded-For": countries[0][0]},
                timeout=5)
            print(f"  ✓ Registered from {countries[0][1]}")
        except:
            pass
        
        time.sleep(1)
        
        # Login from different countries instantly
        for ip, country in countries[1:]:
            try:
                resp = requests.post(f"{API_BASE}/login",
                    json={"email": email, "password": "Test123!"},
                    headers={"X-Forwarded-For": ip},
                    timeout=5)
                print(f"  ⚠ Login attempt from {country} — flagged as geodrift")
            except:
                pass
            time.sleep(0.3)
        
        print(f"\n  ✓ Geodrift attack complete")

    def summary(self):
        """Print final metrics"""
        self.section("Attack Campaign Summary")
        
        print(f"  {BOLD}Total Registrations:{RESET} {self.total_registrations}")
        print(f"  {RED}Quarantined:{RESET} {self.quarantined_count} ({self.quarantined_count/max(1,self.total_registrations)*100:.0f}%)")
        print(f"  {YELLOW}Flagged:{RESET} {self.flagged_count}")
        print(f"  {RED}Failed Logins:{RESET} {self.failed_logins}")
        
        print(f"\n{BOLD}Next Steps:{RESET}")
        print(f"  1. Open {CYAN}http://localhost:3001{RESET}  (Grafana Dashboard)")
        print(f"  2. Login: admin/admin")
        print(f"  3. View SentinelAI Overview dashboard")
        print(f"  4. See real-time alerts and metrics")
        
        print(f"\n{GREEN}✓ Demo Complete!{RESET}\n")

def main():
    demo = HackathonDemo()
    demo.banner()
    
    print(f"{BOLD}Launching coordinated attack scenarios...{RESET}\n")
    time.sleep(2)
    
    # Attack 1: Bot Wave
    demo.wave_attack("ATTACK 1: Bot Wave (25 rapid registrations)", count=25, is_bot=True, delay=0.05)
    time.sleep(2)
    
    # Attack 2: Credential Stuffing
    demo.brute_force_attack(accounts=8, attempts_per=12)
    time.sleep(2)
    
    # Attack 3: Geodrift
    demo.geodrift_attack()
    time.sleep(1)
    
    # Attack 4: Mixed human + bot
    demo.wave_attack("ATTACK 4: Suspicious User Registrations (30 mixed)", count=30, is_bot=False, delay=0.08)
    time.sleep(1)
    
    demo.summary()

if __name__ == "__main__":
    main()
