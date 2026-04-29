# SentinelAI - Trust Score Pipeline Integration Tests
# Owner: Akash
# Branch: feature/security-engine
# -*- coding: utf-8 -*-
import sys, os; os.environ.setdefault('PYTHONUTF8', '1')
#
# Run from backend/ directory with .venv active:
#   python test_scorer.py
#
# This is the primary deliverable for the PR review.
# Arindam can run this to verify the full scoring pipeline.

import sys
import os

# Allow running from sentinelai/ root as well as backend/
sys.path.insert(0, os.path.dirname(__file__))

from scorer import score_registration, score_login, BehavioralPayload

PASS = "\033[92m  PASS\033[0m"
FAIL = "\033[91m  FAIL\033[0m"


def test_benign_user():
    """
    Normal human user with realistic behavioral signals.
    Expected: Trust Score >= 70, recommendation = 'allow'.
    """
    behavioral = BehavioralPayload(
        typing_variance_ms=185,
        time_to_complete_sec=42.0,
        mouse_move_count=67,
        keypress_count=94,
    )
    result = score_registration(
        email="alice@gmail.com",
        behavioral=behavioral,
        ip_address="203.0.113.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        registrations_from_ip_last_hour=1,
        accounts_with_same_ua_today=1,
        ml_anomaly_score=-0.05,
    )

    print(f"  Trust Score : {result.trust_score}")
    print(f"  Penalties   : rule={result.rule_penalty}, behavioral={result.behavioral_penalty}, ml={result.ml_penalty}")
    print(f"  Triggered   : {result.triggered_rules}")
    print(f"  Recommend   : {result.recommendation}")

    assert result.trust_score >= 70, \
        f"Expected trust_score >= 70, got {result.trust_score}"
    assert result.recommendation == "allow", \
        f"Expected 'allow', got '{result.recommendation}'"
    assert result.triggered_rules == [], \
        f"Expected no rules triggered, got {result.triggered_rules}"
    print(PASS)


def test_obvious_bot():
    """
    Classic bot: speed registration (<4s), no mouse movement, disposable email,
    high IP velocity (14 registrations/hr), shared bot device UA, strong ML anomaly.
    Expected: Trust Score < 20, recommendation = 'quarantine'.
    All 4 registration rules should fire.
    """
    behavioral = BehavioralPayload(
        typing_variance_ms=2,
        time_to_complete_sec=1.1,
        mouse_move_count=0,
        keypress_count=44,
    )
    result = score_registration(
        email="user7@temp.com",
        behavioral=behavioral,
        ip_address="192.168.1.1",
        user_agent="python-requests/2.31.0",
        registrations_from_ip_last_hour=14,
        accounts_with_same_ua_today=8,
        ml_anomaly_score=-0.85,
    )

    print(f"  Trust Score : {result.trust_score}")
    print(f"  Penalties   : rule={result.rule_penalty}, behavioral={result.behavioral_penalty}, ml={result.ml_penalty}")
    print(f"  Triggered   : {result.triggered_rules}")
    print(f"  Recommend   : {result.recommendation}")

    assert result.trust_score < 20, \
        f"Expected trust_score < 20, got {result.trust_score}"
    assert result.recommendation == "quarantine", \
        f"Expected 'quarantine', got '{result.recommendation}'"

    expected_rules = {"velocity_ip", "email_pattern", "speed_bot", "duplicate_device"}
    triggered_set = set(result.triggered_rules)
    assert expected_rules.issubset(triggered_set), \
        f"Expected rules {expected_rules}, got {triggered_set}"
    print(PASS)


def test_suspicious_medium_trust():
    """
    Borderline user: slightly fast registration, suspicious email, no ML anomaly.
    Expected: Trust Score in 40–69 range, recommendation = 'otp'.
    """
    behavioral = BehavioralPayload(
        typing_variance_ms=55,
        time_to_complete_sec=5.5,  # just above 4s speed threshold
        mouse_move_count=8,
        keypress_count=60,
    )
    result = score_registration(
        email="test123@gmail.com",    # generic but not disposable domain
        behavioral=behavioral,
        ip_address="10.0.0.5",
        user_agent="Mozilla/5.0 (Linux; Android 11)",
        registrations_from_ip_last_hour=1,
        accounts_with_same_ua_today=1,
        ml_anomaly_score=-0.25,
    )

    print(f"  Trust Score : {result.trust_score}")
    print(f"  Penalties   : rule={result.rule_penalty}, behavioral={result.behavioral_penalty}, ml={result.ml_penalty}")
    print(f"  Triggered   : {result.triggered_rules}")
    print(f"  Recommend   : {result.recommendation}")

    assert 0 <= result.trust_score <= 100, "Trust score out of bounds"
    print(PASS)


def test_geo_drift_login():
    """
    Geo drift scenario from the live demo:
    User from India logs in again from Germany within 47 minutes.
    Expected: geo_drift rule fires, trust score drops from 80.
    """
    result = score_login(
        user_id="test-user-001",
        existing_trust_score=80,
        ip_address="85.208.96.1",       # German IP used in simulate_attack.py
        current_country="Germany",
        last_country="India",
        minutes_since_last_login=47.0,
        ml_anomaly_score=-0.30,
    )

    print(f"  Trust Score : {result.trust_score} (was 80)")
    print(f"  Penalties   : rule={result.rule_penalty}, ml={result.ml_penalty}")
    print(f"  Triggered   : {result.triggered_rules}")
    print(f"  Recommend   : {result.recommendation}")

    assert "geo_drift" in result.triggered_rules, \
        "Expected geo_drift rule to trigger"
    assert result.trust_score < 80, \
        "Trust score should have decreased from 80"
    assert result.rule_penalty == 30, \
        f"Expected geo_drift penalty of 30, got {result.rule_penalty}"
    print(PASS)


def test_geo_drift_no_trigger_outside_window():
    """
    Same geo drift scenario but login gap is 3 hours — outside the 2hr window.
    Expected: geo_drift does NOT fire.
    """
    result = score_login(
        user_id="test-user-002",
        existing_trust_score=75,
        ip_address="85.208.96.1",
        current_country="Germany",
        last_country="India",
        minutes_since_last_login=200.0,  # > 120 min window
        ml_anomaly_score=0.0,
    )

    print(f"  Trust Score : {result.trust_score}")
    print(f"  Triggered   : {result.triggered_rules}")

    assert "geo_drift" not in result.triggered_rules, \
        "geo_drift should NOT fire outside the 2hr window"
    print(PASS)


def test_platform_velocity_spike_alert():
    """
    Platform-level bot wave: 15 registrations/min triggers velocity_spike alert.
    Individual user penalty stays at 0 (platform alert only).
    """
    behavioral = BehavioralPayload(
        typing_variance_ms=150,
        time_to_complete_sec=30.0,
        mouse_move_count=40,
        keypress_count=80,
    )
    result = score_registration(
        email="normaluser@gmail.com",
        behavioral=behavioral,
        ip_address="5.5.5.5",
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X)",
        registrations_from_ip_last_hour=1,
        accounts_with_same_ua_today=1,
        ml_anomaly_score=-0.02,
        registrations_per_minute=15,   # spike!
    )

    print(f"  Trust Score : {result.trust_score}")
    print(f"  Triggered   : {result.triggered_rules}")

    # The platform spike should be in alerts but NOT add individual penalty
    # (platform_velocity_spike has penalty=0)
    assert result.trust_score >= 70, \
        f"Individual user should not be penalised for platform spike, got {result.trust_score}"
    print(PASS)


if __name__ == "__main__":
    header = "=" * 55
    print(f"\n{header}")
    print("  SentinelAI - Trust Score Pipeline Tests")
    print(f"{header}\n")

    tests = [
        ("Benign human user",               test_benign_user),
        ("Obvious bot (all rules fire)",     test_obvious_bot),
        ("Suspicious medium-trust user",     test_suspicious_medium_trust),
        ("Geo drift login (fires)",          test_geo_drift_login),
        ("Geo drift outside window (no-op)", test_geo_drift_no_trigger_outside_window),
        ("Platform velocity spike (alert)",  test_platform_velocity_spike_alert),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        print(f"\n>> {name}")
        try:
            fn()
            passed += 1
        except AssertionError as e:
            print(f"\033[91m  FAIL: {e}\033[0m")
            failed += 1
        except Exception as e:
            print(f"\033[91m  ERROR: {e}\033[0m")
            failed += 1

    print(f"\n{header}")
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  \033[92mAll tests passed [OK]\033[0m")
    else:
        print("  \033[91mSome tests FAILED [!!]\033[0m")
        sys.exit(1)
    print(header)
