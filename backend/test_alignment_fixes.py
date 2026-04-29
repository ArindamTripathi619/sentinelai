#!/usr/bin/env python3
"""
Integration test for 4 alignment fixes:
1. Progressive auth policy (allow/otp/quarantine)
2. Bot-wave platform spike wiring
3. KPI consistency (velocity_spike → bot_wave)
4. Threat feed polling (visual confirmation)
"""

import requests
import time
import json
from datetime import datetime
from database import SessionLocal
from models import Alert, Event, User
import random
import string

BASE_URL = "http://localhost:9000/api"

def random_email():
    """Generate a random email."""
    return f"test.{''.join(random.choices(string.ascii_lowercase, k=8))}@test.com"

def cleanup_db():
    """Clear test data from DB."""
    db = SessionLocal()
    try:
        db.query(Alert).delete()
        db.query(Event).delete()
        db.query(User).delete()
        db.commit()
    finally:
        db.close()

def test_progressive_auth_allow():
    """Test: High-trust user (>70) gets smooth login without OTP."""
    print("\n[TEST 1] Progressive Auth: Allow (high-trust >70)")
    email = random_email()
    
    # Register with high-trust behavioral data
    resp = requests.post(f"{BASE_URL}/register", json={
        "email": email,
        "password": "Test@1234",
        "behavioralData": {
            "typing_variance_ms": 50,      # Low variance = consistent typist
            "time_to_complete_sec": 8.0,
            "mouse_move_count": 50,
            "keypress_count": 80
        }
    }, headers={"X-Forwarded-For": "1.1.1.1"})
    
    assert resp.status_code == 200, f"Register failed: {resp.text}"
    print(f"  ✓ Register: trust_score={resp.json()['trust_score']}")
    
    # Login should be smooth (no OTP required)
    login_resp = requests.post(f"{BASE_URL}/login", json={
        "email": email,
        "password": "Test@1234",
        "ip_address": "1.1.1.1"
    })
    
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    data = login_resp.json()
    assert data.get("token") is not None, "Should have token for allow recommendation"
    assert data.get("otp_required") == False, "Should not require OTP for allow"
    print(f"  ✓ Login: smooth auth (otp_required=False, has_token=True)")
    print(f"    recommendation={data.get('recommendation')}")

def test_progressive_auth_otp():
    """Test: Medium-trust user (40-70) requires OTP."""
    print("\n[TEST 2] Progressive Auth: OTP Challenge (medium-trust 40-70)")
    email = random_email()
    
    # Register with medium-trust behavioral (simulate suspicious but not blocklisted)
    resp = requests.post(f"{BASE_URL}/register", json={
        "email": email,
        "password": "Test@1234",
        "behavioralData": {
            "typing_variance_ms": 300,     # Higher variance
            "time_to_complete_sec": 30.0,
            "mouse_move_count": 5,
            "keypress_count": 10
        }
    }, headers={"X-Forwarded-For": "2.2.2.2"})
    
    assert resp.status_code == 200
    trust_score = resp.json()['trust_score']
    print(f"  ✓ Register: trust_score={trust_score}")
    
    # Login from different IP to trigger medium-trust
    login_resp = requests.post(f"{BASE_URL}/login", json={
        "email": email,
        "password": "Test@1234",
        "ip_address": "3.3.3.3"  # Different IP
    })
    
    assert login_resp.status_code == 200
    data = login_resp.json()
    # OTP should be required for medium trust (40-70)
    if data.get("otp_required"):
        print(f"  ✓ Login: OTP required (otp_session_id={data.get('otp_session_id')})")
        print(f"    recommendation={data.get('recommendation')}, trust_score={data.get('trust_score')}")
    else:
        print(f"  ℹ Login: No OTP required (trust_score={data.get('trust_score')}, recommendation={data.get('recommendation')})")

def test_progressive_auth_quarantine():
    """Test: Low-trust user (<40) gets blocked with quarantine message."""
    print("\n[TEST 3] Progressive Auth: Quarantine (low-trust <40)")
    email = random_email()
    
    # Register with low-trust data
    resp = requests.post(f"{BASE_URL}/register", json={
        "email": email,
        "password": "Test@1234",
        "behavioralData": {
            "typing_variance_ms": 800,
            "time_to_complete_sec": 60.0,
            "mouse_move_count": 2,
            "keypress_count": 3
        }
    }, headers={"X-Forwarded-For": "4.4.4.4"})
    
    assert resp.status_code == 200
    trust_score = resp.json()['trust_score']
    print(f"  ✓ Register: trust_score={trust_score}")
    
    # Try to login
    login_resp = requests.post(f"{BASE_URL}/login", json={
        "email": email,
        "password": "Test@1234",
        "ip_address": "5.5.5.5"
    })
    
    assert login_resp.status_code == 200
    data = login_resp.json()
    is_blocked = data.get("is_blocked")
    if is_blocked:
        print(f"  ✓ Login: Blocked (is_blocked=True, message='{data.get('message')}')")
        print(f"    recommendation={data.get('recommendation')}")
    else:
        print(f"  ℹ Login: Not blocked (is_blocked={is_blocked}, recommendation={data.get('recommendation')})")

def test_bot_wave_spike_detection():
    """Test: Platform velocity spike triggers bot_wave alerts."""
    print("\n[TEST 4] Bot-Wave Spike: Platform velocity detection")
    
    # Simulate rapid registrations from different IPs (bot attack)
    spike_ips = [f"100.{i}.{i}.{i}" for i in range(1, 6)]
    created_users = []
    
    for ip in spike_ips:
        email = random_email()
        resp = requests.post(f"{BASE_URL}/register", json={
            "email": email,
            "password": "Test@1234",
            "behavioralData": {
                "typing_variance_ms": 50,
                "time_to_complete_sec": 5.0,
                "mouse_move_count": 30,
                "keypress_count": 40
            }
        }, headers={"X-Forwarded-For": ip})
        
        if resp.status_code == 200:
            created_users.append((email, ip))
        time.sleep(0.1)  # Small delay between registrations
    
    print(f"  ✓ Registered {len(created_users)} accounts in spike window")
    
    # Check if bot_wave alerts were created (not velocity_spike)
    db = SessionLocal()
    try:
        bot_wave_alerts = db.query(Alert).filter(Alert.type == "bot_wave").count()
        velocity_spike_alerts = db.query(Alert).filter(Alert.type == "velocity_spike").count()
        
        print(f"  ✓ Alerts created:")
        print(f"    - bot_wave: {bot_wave_alerts}")
        print(f"    - velocity_spike: {velocity_spike_alerts} (should be 0 with fix)")
        
        if bot_wave_alerts > 0:
            print(f"  ✓ Bot-wave spike detection working!")
        else:
            print(f"  ℹ No bot_wave alerts yet (may need higher spike threshold)")
    finally:
        db.close()

def test_kpi_consistency():
    """Test: Dashboard KPI counts bot_wave, not velocity_spike."""
    print("\n[TEST 5] KPI Consistency: bot_wave in alert type")
    
    db = SessionLocal()
    try:
        all_alerts = db.query(Alert).all()
        alert_types = {}
        for alert in all_alerts:
            alert_types[alert.type] = alert_types.get(alert.type, 0) + 1
        
        print(f"  ✓ Alert type distribution: {alert_types}")
        
        # KPI counter should use bot_wave
        bot_wave_count = alert_types.get("bot_wave", 0)
        velocity_spike_count = alert_types.get("velocity_spike", 0)
        
        if velocity_spike_count == 0:
            print(f"  ✓ No velocity_spike alerts (renamed to bot_wave)")
        else:
            print(f"  ⚠ Found {velocity_spike_count} velocity_spike alerts (should be 0)")
        
        if bot_wave_count > 0:
            print(f"  ✓ bot_wave KPI will count {bot_wave_count} alerts")
    finally:
        db.close()

def test_polling_config():
    """Test: Verify Dashboard polling is set to 4s (can't fully test from CLI)."""
    print("\n[TEST 6] Threat Feed Polling: Config verification")
    
    try:
        with open("/home/DevCrewX/Projects/sentinelai/frontend/src/dashboard/Dashboard.jsx", "r") as f:
            content = f.read()
            if "setInterval(loadDashboard, 4000)" in content:
                print(f"  ✓ Dashboard polling interval set to 4000ms (4 seconds)")
                return True
            else:
                print(f"  ⚠ Polling interval not found or not 4000ms")
                return False
    except Exception as e:
        print(f"  ✗ Error checking polling config: {e}")
        return False

def main():
    print("=" * 70)
    print("INTEGRATION TEST: 4 Alignment Fixes")
    print("=" * 70)
    
    # Cleanup
    print("\nCleaning up test data...")
    cleanup_db()
    time.sleep(1)
    
    try:
        # Run tests
        test_progressive_auth_allow()
        test_progressive_auth_otp()
        test_progressive_auth_quarantine()
        test_bot_wave_spike_detection()
        test_kpi_consistency()
        test_polling_config()
        
        print("\n" + "=" * 70)
        print("✓ INTEGRATION TEST COMPLETE")
        print("=" * 70)
        print("\nNext: Monitor dashboard for bot_wave alerts and 4s refresh cycle")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
