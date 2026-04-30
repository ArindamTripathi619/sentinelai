#!/usr/bin/env python3
"""
SentinelAI Load Testing Script
Tests backend performance under concurrent registration/login load.
Measures: response times, throughput, error rates, bottlenecks.

Usage:
    python scripts/load_test.py [--sample-size N] [--workers W]

Examples:
    python scripts/load_test.py --sample-size 10 --workers 5      # Small test
    python scripts/load_test.py --sample-size 50 --workers 10     # Medium test
    python scripts/load_test.py --sample-size 100 --workers 20    # Large test
"""

import sys
import argparse
import time
import json
import random
import string
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import httpx

BACKEND_URL = "http://localhost:9000"
REGISTRATION_ENDPOINT = f"{BACKEND_URL}/api/register"
LOGIN_ENDPOINT = f"{BACKEND_URL}/api/login"
HEALTH_ENDPOINT = f"{BACKEND_URL}/api/health"

# Metrics collection
metrics = {
    "registration": {
        "response_times": [],
        "success_count": 0,
        "error_count": 0,
        "errors": defaultdict(int),
    },
    "login": {
        "response_times": [],
        "success_count": 0,
        "error_count": 0,
        "errors": defaultdict(int),
    },
}


def generate_random_email():
    """Generate a random email address."""
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{username}@load-test.local"


def generate_behavioral_payload():
    """Generate realistic behavioral signal payload."""
    return {
        "typing_variance_ms": random.uniform(50, 200),
        "time_to_complete_sec": random.uniform(8, 30),
        "mouse_move_count": random.randint(20, 100),
        "keypress_count": random.randint(40, 150),
        "session_tempo_sec": random.uniform(0.5, 5),
        "mouse_entropy_score": random.uniform(0.3, 0.9),
        "fill_order_score": random.uniform(0.7, 1.0),
    }


def register_user(email: str, password: str = "LoadTest123!") -> dict:
    """Register a user and measure response time."""
    payload = {
        "email": email,
        "password": password,
        "user_agent": "LoadTest/1.0",
        "ip_address": f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
        **generate_behavioral_payload(),
    }

    start_time = time.time()
    try:
        response = requests.post(REGISTRATION_ENDPOINT, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code in [200, 201]:
            metrics["registration"]["success_count"] += 1
            metrics["registration"]["response_times"].append(elapsed)
            return {
                "status": "success",
                "email": email,
                "response_time": elapsed,
                "status_code": response.status_code,
            }
        else:
            metrics["registration"]["error_count"] += 1
            error_msg = response.json().get("detail", "Unknown error")
            metrics["registration"]["errors"][str(response.status_code)] += 1
            return {
                "status": "error",
                "email": email,
                "response_time": elapsed,
                "status_code": response.status_code,
                "error": error_msg,
            }
    except Exception as e:
        elapsed = time.time() - start_time
        metrics["registration"]["error_count"] += 1
        metrics["registration"]["errors"]["exception"] += 1
        return {
            "status": "exception",
            "email": email,
            "response_time": elapsed,
            "error": str(e),
        }


def login_user(email: str, password: str = "LoadTest123!") -> dict:
    """Login a user and measure response time."""
    payload = {
        "email": email,
        "password": password,
        "user_agent": "LoadTest/1.0",
        "ip_address": f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
        **generate_behavioral_payload(),
    }

    start_time = time.time()
    try:
        response = requests.post(LOGIN_ENDPOINT, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code in [200, 201]:
            metrics["login"]["success_count"] += 1
            metrics["login"]["response_times"].append(elapsed)
            return {
                "status": "success",
                "email": email,
                "response_time": elapsed,
                "status_code": response.status_code,
            }
        else:
            metrics["login"]["error_count"] += 1
            error_msg = response.json().get("detail", "Unknown error")
            metrics["login"]["errors"][str(response.status_code)] += 1
            return {
                "status": "error",
                "email": email,
                "response_time": elapsed,
                "status_code": response.status_code,
                "error": error_msg,
            }
    except Exception as e:
        elapsed = time.time() - start_time
        metrics["login"]["error_count"] += 1
        metrics["login"]["errors"]["exception"] += 1
        return {
            "status": "exception",
            "email": email,
            "response_time": elapsed,
            "error": str(e),
        }


def check_backend_health():
    """Verify backend is running."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False


def run_load_test(sample_size: int = 10, workers: int = 5):
    """Run concurrent load test."""
    print(f"\n=== SentinelAI Load Test ===")
    print(f"Sample size: {sample_size} registrations + {sample_size} logins")
    print(f"Concurrent workers: {workers}")
    print(f"Backend: {BACKEND_URL}")
    print()

    # Check backend health
    print("Checking backend health...", end=" ")
    if not check_backend_health():
        print("❌ Backend not responding")
        return False
    print("✅")

    emails = [generate_random_email() for _ in range(sample_size)]

    # Phase 1: Concurrent registrations
    print(f"\n📝 Phase 1: Registering {sample_size} users concurrently...")
    start_phase = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(register_user, email): email for email in emails}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % max(1, sample_size // 10) == 0:
                print(f"  {completed}/{sample_size} registrations completed")
    
    phase1_elapsed = time.time() - start_phase

    # Phase 2: Concurrent logins
    print(f"\n🔐 Phase 2: Logging in {sample_size} users concurrently...")
    start_phase = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(login_user, email): email for email in emails}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % max(1, sample_size // 10) == 0:
                print(f"  {completed}/{sample_size} logins completed")
    
    phase2_elapsed = time.time() - start_phase

    # Metrics summary
    print("\n" + "=" * 50)
    print("📊 LOAD TEST RESULTS")
    print("=" * 50)

    for action_type in ["registration", "login"]:
        stats = metrics[action_type]
        print(f"\n{action_type.upper()}:")
        print(f"  Success:  {stats['success_count']}/{sample_size} ({100*stats['success_count']//sample_size}%)")
        print(f"  Errors:   {stats['error_count']}/{sample_size}")
        
        if stats["errors"]:
            print(f"  Error breakdown:")
            for err, count in stats["errors"].items():
                print(f"    {err}: {count}")
        
        if stats["response_times"]:
            times = stats["response_times"]
            print(f"  Response times:")
            print(f"    Min:     {min(times):.3f}s")
            print(f"    Median:  {statistics.median(times):.3f}s")
            print(f"    Mean:    {statistics.mean(times):.3f}s")
            print(f"    Max:     {max(times):.3f}s")
            if len(times) > 1:
                print(f"    StdDev:  {statistics.stdev(times):.3f}s")
    
    print(f"\n⏱️  PHASE TIMES:")
    print(f"  Registrations: {phase1_elapsed:.2f}s ({sample_size/phase1_elapsed:.1f} req/sec)")
    print(f"  Logins:        {phase2_elapsed:.2f}s ({sample_size/phase2_elapsed:.1f} req/sec)")
    
    total_time = phase1_elapsed + phase2_elapsed
    total_requests = sample_size * 2
    print(f"\n  Total: {total_time:.2f}s ({total_requests/total_time:.1f} req/sec)")

    # Bottleneck analysis
    print(f"\n🔍 BOTTLENECK ANALYSIS:")
    reg_success_rate = metrics["registration"]["success_count"] / sample_size
    login_success_rate = metrics["login"]["success_count"] / sample_size
    
    if reg_success_rate < 0.95:
        print(f"  ⚠️  Registration success rate low: {reg_success_rate:.1%}")
    if login_success_rate < 0.95:
        print(f"  ⚠️  Login success rate low: {login_success_rate:.1%}")
    
    reg_median = statistics.median(metrics["registration"]["response_times"]) if metrics["registration"]["response_times"] else 0
    login_median = statistics.median(metrics["login"]["response_times"]) if metrics["login"]["response_times"] else 0
    
    if reg_median > 5:
        print(f"  ⚠️  Registration response times high: {reg_median:.2f}s median")
    if login_median > 5:
        print(f"  ⚠️  Login response times high: {login_median:.2f}s median")
    
    print("\n✅ Load test completed")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelAI Load Test")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of users to simulate (default: 10)")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent workers (default: 5)")
    
    args = parser.parse_args()
    
    success = run_load_test(sample_size=args.sample_size, workers=args.workers)
    sys.exit(0 if success else 1)
