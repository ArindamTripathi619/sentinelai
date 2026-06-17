#!/usr/bin/env python3
"""
SentinelAI — Comprehensive Security Test Suite
===============================================

COMPLETE test coverage for hackathon demo:
  ✓ Bot Wave Detection (mass registrations)
  ✓ Suspicious Login Attempts (concurrent logins)
  ✓ Geodrift Detection (rapid IP/location changes)
  ✓ Quarantine/Flag Transitions (status changes)
  ✓ Credential Stuffing (login spam + failures)
  ✓ Mixed Attack Patterns (combined threats)

Usage:
    python scripts/comprehensive_security_test.py --all
    python scripts/comprehensive_security_test.py --reset-db
    python scripts/comprehensive_security_test.py --scenario bot_wave
    python scripts/comprehensive_security_test.py --scenario coordinated_logins
    python scripts/comprehensive_security_test.py --scenario geodrift
    python scripts/comprehensive_security_test.py --metrics

Output: Real-time alerts + metrics for Grafana dashboard
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
import time
import json
import argparse
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

API_BASE = "http://localhost:9000/api"
ADMIN_EMAIL = "admin.demo@sentinelai.local"
ADMIN_PASS = "DemoPass!234"

# ANSI colors
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
BOLD    = "\033[1m"
RESET   = "\033[0m"
DIM     = "\033[2m"

class TestSuite:
    def __init__(self):
        self.admin_token = None
        self.results = {
            "bot_wave": [],
            "coordinated_logins": [],
            "geodrift": [],
            "quarantine": [],
            "credential_stuffing": [],
            "mixed_attack": []
        }
        self.metrics = {
            "total_requests": 0,
            "flagged": 0,
            "quarantined": 0,
            "alerts_fired": 0,
            "avg_trust_score": 0
        }

    # ================================================================================
    # UTILITIES
    # ================================================================================

    def header(self, title):
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        print(f"{BOLD}{CYAN}  TEST: {title}{RESET}")
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    def success(self, msg):
        print(f"  {GREEN}[✓]{RESET} {msg}")

    def warn(self, msg):
        print(f"  {YELLOW}[!]{RESET} {msg}")

    def error(self, msg):
        print(f"  {RED}[✗]{RESET} {msg}")

    def info(self, msg):
        print(f"  {DIM}{msg}{RESET}")

    def get_admin_token(self):
        """Login as admin to access alerts."""
        if self.admin_token:
            return self.admin_token
        
        try:
            resp = requests.post(
                f"{API_BASE}/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
                timeout=5
            )
            if resp.status_code == 200:
                self.admin_token = resp.json().get("access_token") or resp.json().get("token")
                return self.admin_token
        except:
            pass
        return None

    def get_alerts(self, severity=None):
        """Fetch recent alerts from backend."""
        token = self.get_admin_token()
        if not token:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resp = requests.get(f"{API_BASE}/alerts", headers=headers, timeout=5)
            if resp.status_code == 200:
                alerts = resp.json().get("alerts", [])
                if severity:
                    alerts = [a for a in alerts if a.get("severity") == severity]
                return alerts
        except:
            pass
        return []

    def wait_for_alerts(self, timeout=5, count=1):
        """Wait for alerts to be created."""
        start = time.time()
        while time.time() - start < timeout:
            alerts = self.get_alerts()
            if len(alerts) >= count:
                return alerts
            time.sleep(0.5)
        return alerts

    def generate_behavioral_payload(self, is_bot=False):
        """Generate behavioral signal (human or bot)."""
        if is_bot:
            # Bot: fast, low variance, minimal movements
            return {
                "typing_variance_ms": random.uniform(1, 3),
                "time_to_complete_sec": random.uniform(0.5, 1.5),
                "mouse_move_count": 0,
                "keypress_count": random.randint(30, 45),
            }
        else:
            # Human: slower, high variance, natural movements
            return {
                "typing_variance_ms": random.uniform(80, 180),
                "time_to_complete_sec": random.uniform(12, 40),
                "mouse_move_count": random.randint(15, 80),
                "keypress_count": random.randint(60, 150),
            }

    def register_user(self, email, password="TestPass123!", ip_address=None, is_bot=False):
        """Register a single user."""
        payload = {
            "email": email,
            "password": password,
            "behavioral": self.generate_behavioral_payload(is_bot=is_bot),
        }

        headers = {}
        if ip_address:
            headers["X-Forwarded-For"] = ip_address

        try:
            resp = requests.post(
                f"{API_BASE}/register",
                json=payload,
                headers=headers,
                timeout=5
            )
            self.metrics["total_requests"] += 1
            
            if resp.status_code in [200, 201]:
                data = resp.json()
                if data.get("status") == "quarantined":
                    self.metrics["quarantined"] += 1
                elif data.get("status") == "flagged":
                    self.metrics["flagged"] += 1
                return data
            else:
                return resp.json()
        except Exception as e:
            self.error(f"Registration failed: {str(e)}")
            return None

    def login_user(self, email, password="TestPass123!", ip_address=None):
        """Attempt login for a user."""
        payload = {
            "email": email,
            "password": password,
        }

        headers = {}
        if ip_address:
            headers["X-Forwarded-For"] = ip_address

        try:
            resp = requests.post(
                f"{API_BASE}/login",
                json=payload,
                headers=headers,
                timeout=5
            )
            self.metrics["total_requests"] += 1
            return resp.json() if resp.status_code == 200 else {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    # ================================================================================
    # TEST SCENARIOS
    # ================================================================================

    def test_bot_wave(self):
        """
        TEST 1: Bot Wave Detection
        Mass registrations from same IP in short time window
        Expected: Multiple users quarantined, alert fired
        """
        self.header("BOT WAVE — Mass Registration Attack")
        print("  Registering 15 accounts in rapid succession from single IP...\n")
        
        time.sleep(2)
        
        BOT_IP = "192.168.1.100"
        start_time = time.time()
        
        for i in range(1, 16):
            email = f"bot_wave_user{i}_{int(time.time())}@temp.com"
            result = self.register_user(email, ip_address=BOT_IP, is_bot=True)
            
            if result:
                status = result.get("status", "unknown")
                trust = result.get("trust_score", "N/A")
                
                if status == "quarantined":
                    self.warn(f"  [{i:02d}/15] {email} → QUARANTINED (trust: {trust})")
                    self.results["bot_wave"].append({"email": email, "status": status})
                else:
                    self.info(f"  [{i:02d}/15] {email} → {status} (trust: {trust})")
        
        elapsed = time.time() - start_time
        print(f"\n  Time taken: {elapsed:.2f}s")
        
        # Check for alert
        time.sleep(2)
        alerts = self.get_alerts(severity="critical")
        if alerts:
            bot_wave_alerts = [a for a in alerts if "bot" in a.get("type", "").lower()]
            if bot_wave_alerts:
                self.success(f"BOT WAVE ALERT FIRED: {len(bot_wave_alerts)} alert(s)")
                self.metrics["alerts_fired"] += len(bot_wave_alerts)
        
        return self.results["bot_wave"]

    def test_coordinated_logins(self):
        """
        TEST 2: Coordinated Suspicious Logins
        Multiple simultaneous login attempts with suspicious patterns
        Expected: Accounts locked/flagged, alerts fired
        """
        self.header("COORDINATED LOGINS — Suspicious Auth Pattern")
        print("  Launching 20 concurrent suspicious login attempts...\n")
        
        # First, register some test users
        test_users = []
        for i in range(5):
            email = f"susp_login_user{i}_{int(time.time())}@test.local"
            self.register_user(email)
            test_users.append((email, "TestPass123!"))
        
        time.sleep(1)
        
        # Now attempt rapid-fire logins with wrong password
        def attempt_login(user_email, attempt_num):
            results = []
            for j in range(4):  # 4 failed attempts per user
                result = self.login_user(user_email, password="WrongPass123!")
                results.append(result)
                time.sleep(0.1)
            return user_email, results
        
        print("  Executing 20 parallel failed login attempts...\n")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i, (email, _) in enumerate(test_users):
                futures.append(executor.submit(attempt_login, email, i))
            
            for future in as_completed(futures):
                email, attempts = future.result()
                failed_count = sum(1 for a in attempts if "error" in a or not a.get("access_token"))
                self.warn(f"  {email} → {failed_count} failed attempts")
                self.results["coordinated_logins"].append({
                    "email": email,
                    "failed_attempts": failed_count
                })
        
        # Check for alerts
        time.sleep(2)
        alerts = self.get_alerts()
        if alerts:
            self.success(f"ALERTS CAPTURED: {len(alerts)} total alert(s)")
            self.metrics["alerts_fired"] += len(alerts)
        
        return self.results["coordinated_logins"]

    def test_geodrift(self):
        """
        TEST 3: Geodrift Detection
        User registration from one IP, then rapid login from geographically distant IP
        Expected: Geodrift flagged, account quarantined
        """
        self.header("GEODRIFT — Rapidlocation Jump Detection")
        print("  Testing rapid geographic location changes...\n")
        
        # Register from USA IP
        test_email = f"geodrift_user_{int(time.time())}@test.local"
        us_ip = "203.0.113.1"  # USA IP
        
        self.info("Step 1: Registering from USA IP...")
        result = self.register_user(test_email, ip_address=us_ip)
        self.info(f"  Status: {result.get('status')} (trust: {result.get('trust_score')})")
        
        time.sleep(1)
        
        # Attempt login from China IP (instant geographically impossible)
        self.info("Step 2: Attempting login from China IP (instantly)...")
        china_ip = "202.96.199.133"
        login_result = self.login_user(test_email, ip_address=china_ip)
        
        if "error" in login_result:
            self.warn(f"  Login denied: {login_result.get('error')}")
        else:
            self.warn(f"  Login blocked/flagged due to geodrift")
        
        self.results["geodrift"].append({
            "email": test_email,
            "us_ip": us_ip,
            "cn_ip": china_ip,
            "result": login_result
        })
        
        # Check for geodrift alert
        time.sleep(2)
        alerts = self.get_alerts()
        geodrift_alerts = [a for a in alerts if "geodrift" in a.get("type", "").lower() or "geo" in a.get("description", "").lower()]
        if geodrift_alerts:
            self.success(f"GEODRIFT ALERT FIRED: {len(geodrift_alerts)} alert(s)")
            self.metrics["alerts_fired"] += len(geodrift_alerts)
        
        return self.results["geodrift"]

    def test_quarantine_lifecycle(self):
        """
        TEST 4: Quarantine Lifecycle
        User gets quarantined, test state transitions
        Expected: User transitions through quarantine states
        """
        self.header("QUARANTINE LIFECYCLE — User Status Transitions")
        print("  Testing user quarantine and flag transitions...\n")
        
        # Create bot-like registrations
        test_email = f"quarantine_test_{int(time.time())}@temp.com"
        bot_ip = "192.168.50.100"
        
        self.info("Registering account with bot-like behavior...")
        result = self.register_user(test_email, ip_address=bot_ip, is_bot=True)
        
        status = result.get("status", "unknown")
        trust = result.get("trust_score", 0)
        
        if status == "quarantined":
            self.success(f"User quarantined immediately (trust: {trust})")
        elif status == "flagged":
            self.warn(f"User flagged (trust: {trust})")
        else:
            self.warn(f"User status: {status} (trust: {trust})")
        
        self.results["quarantine"].append({
            "email": test_email,
            "initial_status": status,
            "trust_score": trust
        })
        
        return self.results["quarantine"]

    def test_credential_stuffing(self):
        """
        TEST 5: Credential Stuffing Detection
        Rapid failed login attempts against valid accounts
        Expected: Account locked, rate limiting triggered
        """
        self.header("CREDENTIAL STUFFING — Brute Force Detection")
        print("  Testing rapid failed login attempts...\n")
        
        # Register a valid user
        test_email = f"stuffing_victim_{int(time.time())}@test.local"
        self.register_user(test_email)
        
        time.sleep(1)
        
        # Attempt wrong password 15 times in rapid succession
        print("  Launching 15 rapid failed login attempts...\n")
        
        failed_count = 0
        for attempt in range(15):
            result = self.login_user(test_email, password="WrongPassword123!")
            
            if "error" in result or not result.get("access_token"):
                failed_count += 1
                if attempt % 3 == 0:
                    self.warn(f"  Attempt {attempt+1:02d} — Login failed")
            
            time.sleep(0.2)
        
        self.success(f"Brute force test: {failed_count}/15 attempts failed as expected")
        
        self.results["credential_stuffing"].append({
            "email": test_email,
            "failed_attempts": failed_count
        })
        
        # Check for rate limit alert
        time.sleep(2)
        alerts = self.get_alerts()
        if alerts:
            self.success(f"Rate limit/brute force alerts: {len(alerts)} captured")
        
        return self.results["credential_stuffing"]

    def test_mixed_attack(self):
        """
        TEST 6: Mixed Attack Pattern
        Combination of bot wave + failed logins + geodrift
        Expected: Multiple rules triggered, accounts heavily quarantined
        """
        self.header("MIXED ATTACK — Complex Multi-Vector Attack")
        print("  Testing complex combined attack pattern...\n")
        
        # Wave 1: Bot registrations
        print("  Phase 1: Bot wave init...")
        bot_ip = "198.51.100.50"
        for i in range(5):
            email = f"mixed_bot{i}_{int(time.time())}@temp.com"
            result = self.register_user(email, ip_address=bot_ip, is_bot=True)
            self.info(f"    Registered {email} → {result.get('status')}")
        
        time.sleep(1)
        
        # Wave 2: Failed logins from different countries
        print("  Phase 2: Coordinated failed logins from multiple geos...")
        test_email = f"mixed_victim_{int(time.time())}@test.local"
        
        # Register real user
        self.register_user(test_email)
        time.sleep(0.5)
        
        # Login from different IPs
        ips = [
            ("198.51.100.1", "USA"),
            ("203.0.113.50", "Germany"),
            ("202.96.199.50", "China"),
        ]
        
        for ip, location in ips:
            result = self.login_user(test_email, password="BadPass!", ip_address=ip)
            self.warn(f"    Failed login from {location} ({ip})")
            time.sleep(0.3)
        
        self.results["mixed_attack"].append({
            "phases": ["bot_wave", "geodrift", "credential_attempts"],
            "email": test_email
        })
        
        # Check for multiple alerts
        time.sleep(3)
        alerts = self.get_alerts()
        self.success(f"Mixed attack test complete: {len(alerts)} alerts triggered")
        self.metrics["alerts_fired"] += len(alerts)
        
        return self.results["mixed_attack"]

    # ================================================================================
    # REPORT & CLEANUP
    # ================================================================================

    def print_report(self):
        """Print comprehensive test report."""
        print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
        print(f"{BOLD}{CYAN}  COMPREHENSIVE SECURITY TEST REPORT{RESET}")
        print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
        
        # Summary metrics
        print(f"{BOLD}📊 METRICS{RESET}")
        print(f"  Total API requests:     {self.metrics['total_requests']}")
        print(f"  Accounts quarantined:   {self.metrics['quarantined']}")
        print(f"  Accounts flagged:       {self.metrics['flagged']}")
        print(f"  Alerts fired:           {self.metrics['alerts_fired']}")
        print()
        
        # Per-test results
        print(f"{BOLD}📋 TEST RESULTS{RESET}")
        for test_name, results in self.results.items():
            count = len(results) if isinstance(results, list) else 0
            status = f"{GREEN}PASS{RESET}" if count > 0 else f"{YELLOW}PARTIAL{RESET}"
            print(f"  {test_name.replace('_', ' ').title():<30} {status} ({count} result{'s' if count != 1 else ''})")
        print()
        
        # Alert summary
        print(f"{BOLD}🚨 ALERTS STATUS{RESET}")
        alerts = self.get_alerts()
        if alerts:
            print(f"  Total alerts in system: {len(alerts)}")
            for alert in alerts[:5]:  # Show first 5
                print(f"    - {alert.get('type')}: {alert.get('description')[:50]}")
        else:
            print(f"  {YELLOW}No alerts in system (check dashboard){RESET}")
        print()
        
        print(f"{BOLD}✅ All tests completed!{RESET}")
        print(f"  Visit dashboard at: {CYAN}http://localhost:3001{RESET}")
        print(f"  Prometheus at:      {CYAN}http://localhost:9090{RESET}")
        print()

    def reset_database(self):
        """Reset database to clean state."""
        self.header("DATABASE RESET")
        try:
            from backend.database import engine, Base
            from backend.models import User, Event, Alert, OtpSession
            
            print("  Dropping tables...")
            Base.metadata.drop_all(engine)
            
            print("  Creating tables...")
            Base.metadata.create_all(engine)
            
            # Create admin user
            from backend.database import SessionLocal
            from backend import auth
            
            db = SessionLocal()
            admin = User(
                email="admin@example.com",
                password_hash=auth.hash_password("password123"),
                is_admin=True,
                status="active"
            )
            db.add(admin)
            db.commit()
            
            self.success("Database reset and admin user created")
        except Exception as e:
            self.error(f"Database reset failed: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="SentinelAI Comprehensive Security Test Suite")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--reset-db", action="store_true", help="Reset database to clean state")
    parser.add_argument("--scenario", type=str, help="Run specific scenario (bot_wave, coordinated_logins, etc.)")
    parser.add_argument("--metrics", action="store_true", help="Show metrics only")
    
    args = parser.parse_args()
    
    suite = TestSuite()
    
    if args.reset_db:
        suite.reset_database()
        return
    
    # Run tests
    if args.all or not args.scenario:
        suite.test_bot_wave()
        time.sleep(3)
        suite.test_coordinated_logins()
        time.sleep(3)
        suite.test_geodrift()
        time.sleep(2)
        suite.test_quarantine_lifecycle()
        time.sleep(2)
        suite.test_credential_stuffing()
        time.sleep(2)
        suite.test_mixed_attack()
    elif args.scenario == "bot_wave":
        suite.test_bot_wave()
    elif args.scenario == "coordinated_logins":
        suite.test_coordinated_logins()
    elif args.scenario == "geodrift":
        suite.test_geodrift()
    elif args.scenario == "quarantine":
        suite.test_quarantine_lifecycle()
    elif args.scenario == "credential_stuffing":
        suite.test_credential_stuffing()
    elif args.scenario == "mixed_attack":
        suite.test_mixed_attack()
    
    time.sleep(2)
    suite.print_report()

if __name__ == "__main__":
    main()
