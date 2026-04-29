# SentinelAI - Rules Engine Unit Tests
# Owner: Akash
# Branch: feature/security-engine
# -*- coding: utf-8 -*-
import sys, os; os.environ.setdefault('PYTHONUTF8', '1')
#
# Run from backend/ directory with .venv active:
#   python test_rules.py
#
# Tests each rule function independently, then the aggregate runners.

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from rules import (
    check_velocity_ip,
    check_email_pattern,
    check_speed_bot,
    check_duplicate_device,
    check_geo_drift,
    check_platform_velocity_spike,
    run_registration_rules,
    run_login_rules,
)

PASS = "\033[92m  PASS\033[0m"
FAIL_PREFIX = "\033[91m  FAIL"
RESET = "\033[0m"


def assert_rule(condition: bool, msg: str):
    if not condition:
        raise AssertionError(msg)


# ---------------------------------------------------------------------------
# check_velocity_ip
# ---------------------------------------------------------------------------
def test_velocity_ip():
    # Should trigger above limit (3)
    r = check_velocity_ip("1.2.3.4", 14)
    assert_rule(r.triggered, "Expected triggered=True for 14 registrations")
    assert_rule(r.penalty == 25, f"Expected penalty=25, got {r.penalty}")
    assert_rule(r.alert_type == "bot_wave", f"Expected alert_type='bot_wave', got {r.alert_type}")
    assert_rule(r.alert_severity == "critical", f"Expected severity='critical'")

    # Should NOT trigger at or below limit
    r2 = check_velocity_ip("1.2.3.4", 3)
    assert_rule(not r2.triggered, "Expected triggered=False for exactly 3 registrations")
    assert_rule(r2.penalty == 0, f"Expected penalty=0, got {r2.penalty}")

    r3 = check_velocity_ip("1.2.3.4", 0)
    assert_rule(not r3.triggered, "Expected triggered=False for 0 registrations")
    print(PASS)


# ---------------------------------------------------------------------------
# check_email_pattern
# ---------------------------------------------------------------------------
def test_email_pattern():
    # Disposable domains — should trigger
    disposable_cases = [
        "someone@temp.com",
        "x@mailinator.com",
        "y@guerrillamail.com",
        "z@trashmail.me",
        "a@yopmail.com",
        "b@maildrop.cc",
        "c@spam4.me",
    ]
    for email in disposable_cases:
        r = check_email_pattern(email)
        assert_rule(r.triggered, f"Expected flag for disposable: {email}")
        assert_rule(r.penalty == 20, f"Expected penalty=20 for {email}")

    # Sequential patterns — should trigger
    sequential_cases = [
        "user7@example.com",
        "test99@example.com",
        "bot3@example.com",
        "fake1@example.com",
        "admin2@example.com",
        "demo5@example.com",
        "123456@example.com",      # purely numeric
        "name1234@example.com",    # base + 4 digits
    ]
    for email in sequential_cases:
        r = check_email_pattern(email)
        assert_rule(r.triggered, f"Expected flag for sequential: {email}")

    # Legitimate emails — should NOT trigger
    clean_cases = [
        "alice@gmail.com",
        "john.doe@university.edu",
        "akash@sentinelai.dev",
        "support@company.co.uk",
        "user@outlook.com",
    ]
    for email in clean_cases:
        r = check_email_pattern(email)
        assert_rule(not r.triggered, f"Expected no flag for clean email: {email}")
        assert_rule(r.penalty == 0, f"Expected penalty=0 for {email}")
    print(PASS)


# ---------------------------------------------------------------------------
# check_speed_bot
# ---------------------------------------------------------------------------
def test_speed_bot():
    # Below threshold — should trigger
    for t in [0.5, 1.1, 1.9, 2.9]:
        r = check_speed_bot(t)
        assert_rule(r.triggered, f"Expected triggered=True for {t}s")
        assert_rule(r.penalty == 20, f"Expected penalty=20 for {t}s")
        assert_rule(r.alert_type == "speed_bot", f"Expected alert_type='speed_bot'")

    # At or above threshold — should NOT trigger
    for t in [3.0, 4.0, 10.0, 45.0, 120.0]:
        r = check_speed_bot(t)
        assert_rule(not r.triggered, f"Expected triggered=False for {t}s")
        assert_rule(r.penalty == 0, f"Expected penalty=0 for {t}s")
    print(PASS)


# ---------------------------------------------------------------------------
# check_duplicate_device
# ---------------------------------------------------------------------------
def test_duplicate_device():
    ua = "python-requests/2.31.0"

    # At or above limit (3) — should trigger
    for count in [3, 5, 10]:
        r = check_duplicate_device(ua, count)
        assert_rule(r.triggered, f"Expected triggered=True for count={count}")
        assert_rule(r.penalty == 15, f"Expected penalty=15, got {r.penalty}")

    # Below limit — should NOT trigger
    for count in [0, 1, 2]:
        r = check_duplicate_device(ua, count)
        assert_rule(not r.triggered, f"Expected triggered=False for count={count}")
        assert_rule(r.penalty == 0, f"Expected penalty=0 for count={count}")
    print(PASS)


# ---------------------------------------------------------------------------
# check_geo_drift
# ---------------------------------------------------------------------------
def test_geo_drift():
    uid = "test-user-001"

    # Different country within window — should trigger
    r = check_geo_drift(uid, "Germany", "India", 47.0)
    assert_rule(r.triggered, "Expected triggered=True for India→Germany in 47min")
    assert_rule(r.penalty == 30, f"Expected penalty=30, got {r.penalty}")
    assert_rule(r.alert_type == "geo_drift", f"Expected alert_type='geo_drift'")

    # Same country — should NOT trigger
    r2 = check_geo_drift(uid, "India", "India", 30.0)
    assert_rule(not r2.triggered, "Expected triggered=False for same country")
    assert_rule(r2.penalty == 0, f"Expected penalty=0")

    # Different country but OUTSIDE the 2hr window — should NOT trigger
    r3 = check_geo_drift(uid, "Germany", "India", 200.0)
    assert_rule(not r3.triggered, "Expected triggered=False for gap > 120 min")
    assert_rule(r3.penalty == 0, f"Expected penalty=0")

    # No previous login — should NOT trigger
    r4 = check_geo_drift(uid, "Germany", None, None)
    assert_rule(not r4.triggered, "Expected triggered=False when no last login data")
    print(PASS)


# ---------------------------------------------------------------------------
# check_platform_velocity_spike
# ---------------------------------------------------------------------------
def test_platform_velocity_spike():
    # Above limit (10) — should trigger alert, penalty = 0
    r = check_platform_velocity_spike(15)
    assert_rule(r.triggered, "Expected triggered=True for 15 reg/min")
    assert_rule(r.penalty == 0, f"Expected penalty=0 (platform alert only), got {r.penalty}")
    assert_rule(r.alert_type == "velocity_spike", f"Expected alert_type='velocity_spike'")
    assert_rule(r.alert_severity == "high", f"Expected severity='high'")

    # At or below limit — should NOT trigger
    for rate in [0, 5, 10]:
        r2 = check_platform_velocity_spike(rate)
        assert_rule(not r2.triggered, f"Expected triggered=False for {rate}/min")
    print(PASS)


# ---------------------------------------------------------------------------
# run_registration_rules (aggregated)
# ---------------------------------------------------------------------------
def test_aggregate_registration_all_rules_fire():
    """All 4 individual rules + velocity spike should fire for a worst-case bot."""
    out = run_registration_rules(
        email="user7@temp.com",
        time_to_complete_sec=1.5,          # speed_bot
        ip_address="192.168.1.1",
        user_agent="python-requests/2.31.0",
        registrations_from_ip_last_hour=10, # velocity_ip
        accounts_with_same_ua_today=5,      # duplicate_device
        registrations_per_minute=15,        # platform_velocity_spike (alert only)
    )
    # email_pattern fires for user7@temp.com
    assert_rule("velocity_ip" in out.triggered_rules, "velocity_ip should fire")
    assert_rule("email_pattern" in out.triggered_rules, "email_pattern should fire")
    assert_rule("speed_bot" in out.triggered_rules, "speed_bot should fire")
    assert_rule("duplicate_device" in out.triggered_rules, "duplicate_device should fire")
    assert_rule("platform_velocity_spike" in out.triggered_rules, "platform_velocity_spike should fire")

    # penalty = 25 + 20 + 20 + 15 = 80 (platform spike = 0)
    assert_rule(out.total_penalty == 80, f"Expected total_penalty=80, got {out.total_penalty}")

    # Alerts should be created
    alert_types = {a.alert_type for a in out.alerts_to_create}
    assert_rule("bot_wave" in alert_types, "bot_wave alert missing")
    assert_rule("speed_bot" in alert_types, "speed_bot alert missing")
    assert_rule("velocity_spike" in alert_types, "velocity_spike alert missing")
    print(PASS)


def test_aggregate_registration_clean_user():
    """Clean user — no rules should fire."""
    out = run_registration_rules(
        email="alice@gmail.com",
        time_to_complete_sec=42.0,
        ip_address="203.0.113.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0)",
        registrations_from_ip_last_hour=1,
        accounts_with_same_ua_today=1,
        registrations_per_minute=2,
    )
    assert_rule(out.total_penalty == 0, f"Expected penalty=0, got {out.total_penalty}")
    assert_rule(out.triggered_rules == [], f"Expected no triggered rules, got {out.triggered_rules}")
    assert_rule(out.alerts_to_create == [], f"Expected no alerts, got {out.alerts_to_create}")
    print(PASS)


# ---------------------------------------------------------------------------
# run_login_rules (aggregated)
# ---------------------------------------------------------------------------
def test_aggregate_login_geo_drift():
    out = run_login_rules(
        user_id="u1",
        ip_address="85.208.96.1",
        current_country="Germany",
        last_country="India",
        minutes_since_last_login=47.0,
    )
    assert_rule("geo_drift" in out.triggered_rules, "geo_drift should fire")
    assert_rule(out.total_penalty == 30, f"Expected penalty=30, got {out.total_penalty}")
    print(PASS)


def test_aggregate_login_no_drift():
    out = run_login_rules(
        user_id="u2",
        ip_address="203.0.113.1",
        current_country="India",
        last_country="India",
        minutes_since_last_login=30.0,
    )
    assert_rule(out.total_penalty == 0, f"Expected penalty=0, got {out.total_penalty}")
    print(PASS)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    header = "=" * 55
    print(f"\n{header}")
    print("  SentinelAI \u2014 Rules Engine Unit Tests")
    print(f"{header}\n")

    tests = [
        ("check_velocity_ip",                         test_velocity_ip),
        ("check_email_pattern",                        test_email_pattern),
        ("check_speed_bot",                            test_speed_bot),
        ("check_duplicate_device",                     test_duplicate_device),
        ("check_geo_drift",                            test_geo_drift),
        ("check_platform_velocity_spike",              test_platform_velocity_spike),
        ("run_registration_rules (all rules fire)",    test_aggregate_registration_all_rules_fire),
        ("run_registration_rules (clean user)",        test_aggregate_registration_clean_user),
        ("run_login_rules (geo drift fires)",          test_aggregate_login_geo_drift),
        ("run_login_rules (same country, no drift)",   test_aggregate_login_no_drift),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f">> {name}")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"{FAIL_PREFIX}: {e}{RESET}")
            failed += 1
        except Exception as e:
            print(f"{FAIL_PREFIX} (ERROR): {e}{RESET}")
            failed += 1

    print(f"\n{header}")
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  \033[92mAll rules tests passed [OK]\033[0m")
    else:
        print("  \033[91mSome tests FAILED [!!]\033[0m")
        sys.exit(1)
    print(header)
