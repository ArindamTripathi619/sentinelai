#!/usr/bin/env python3
"""
SentinelAI project-wide test suite.

Run from the repository root:
  python tests/project_suite.py

This suite covers:
- project configuration and dev-port alignment
- rules/scoring/ML contracts
- live backend/frontend smoke checks when services are available
"""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

os.environ.setdefault("ML_MODEL_PATH", str(BACKEND_DIR / "ml_model.pkl"))

sys.path.insert(0, str(BACKEND_DIR))

from rules import (  # noqa: E402
    check_email_pattern,
    check_geo_drift,
    check_platform_velocity_spike,
    check_speed_bot,
    check_velocity_ip,
    run_login_rules,
    run_registration_rules,
)
from scorer import BehavioralPayload, score_login, score_registration  # noqa: E402
from ml_model import build_feature_vector, load_model, predict  # noqa: E402


BACKEND_BASE = os.getenv("SENTINELAI_BACKEND_URL", "http://127.0.0.1:9000")
FRONTEND_BASE = os.getenv("SENTINELAI_FRONTEND_URL", "http://127.0.0.1:3000")
API_BASE = f"{BACKEND_BASE}/api"


def _read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _service_is_up(url: str) -> bool:
    try:
        response = requests.get(url, timeout=2)
        return response.ok
    except requests.RequestException:
        return False


class TestProjectConfig(unittest.TestCase):
    def test_frontend_dev_port_is_3000(self):
        vite_config = _read_text("frontend/vite.config.js")
        self.assertIn("port: 3000", vite_config)

    def test_backend_docs_use_9000(self):
        backend_readme = _read_text("backend/README.md")
        self.assertIn("uvicorn main:app --reload --port 9000", backend_readme)
        self.assertIn("http://localhost:9000/docs", backend_readme)

    def test_root_docs_use_9000_and_3000(self):
        readme = _read_text("README.md")
        self.assertIn("uvicorn main:app --reload --port 9000", readme)
        self.assertIn("http://localhost:9000", readme)
        self.assertIn("http://localhost:3000", readme)

    def test_api_contract_points_to_9000(self):
        api_doc = _read_text("API.md")
        self.assertIn("http://localhost:9000/api", api_doc)


class TestRulesAndScoring(unittest.TestCase):
    def test_rule_contracts(self):
        self.assertTrue(check_velocity_ip("1.2.3.4", 14).triggered)
        self.assertTrue(check_email_pattern("user7@temp.com").triggered)
        self.assertTrue(check_speed_bot(1.2).triggered)
        self.assertTrue(check_geo_drift("u1", "Germany", "India", 47.0).triggered)
        self.assertTrue(check_platform_velocity_spike(15).triggered)

    def test_aggregate_rules_contracts(self):
        registration = run_registration_rules(
            email="user7@temp.com",
            time_to_complete_sec=1.5,
            ip_address="192.168.1.1",
            user_agent="python-requests/2.31.0",
            registrations_from_ip_last_hour=10,
            accounts_with_same_ua_today=5,
            registrations_per_minute=15,
        )
        self.assertIn("velocity_ip", registration.triggered_rules)
        self.assertIn("email_pattern", registration.triggered_rules)
        self.assertIn("speed_bot", registration.triggered_rules)
        self.assertIn("duplicate_device", registration.triggered_rules)

        login = run_login_rules(
            user_id="u1",
            ip_address="85.208.96.1",
            current_country="Germany",
            last_country="India",
            minutes_since_last_login=47.0,
        )
        self.assertIn("geo_drift", login.triggered_rules)

    def test_score_registration_and_login(self):
        benign = BehavioralPayload(
            typing_variance_ms=180,
            time_to_complete_sec=45.0,
            mouse_move_count=55,
            keypress_count=95,
            session_tempo_sec=5.0,
            mouse_entropy_score=0.8,
            fill_order_score=0.95,
        )
        benign_score = score_registration(
            email="alice@gmail.com",
            behavioral=benign,
            ip_address="203.0.113.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0)",
            registrations_from_ip_last_hour=1,
            accounts_with_same_ua_today=1,
            ml_anomaly_score=-0.05,
        )
        self.assertGreaterEqual(benign_score.trust_score, 70)
        self.assertEqual(benign_score.recommendation, "allow")

        bot = BehavioralPayload(
            typing_variance_ms=2,
            time_to_complete_sec=1.1,
            mouse_move_count=0,
            keypress_count=44,
            session_tempo_sec=1.0,
            mouse_entropy_score=0.05,
            fill_order_score=0.1,
        )
        bot_score = score_registration(
            email="user7@temp.com",
            behavioral=bot,
            ip_address="192.168.1.1",
            user_agent="python-requests/2.31.0",
            registrations_from_ip_last_hour=14,
            accounts_with_same_ua_today=8,
            ml_anomaly_score=-0.85,
        )
        self.assertLess(bot_score.trust_score, 20)
        self.assertEqual(bot_score.recommendation, "quarantine")

        login_score = score_login(
            user_id="test-user-001",
            existing_trust_score=80,
            ip_address="85.208.96.1",
            current_country="Germany",
            last_country="India",
            minutes_since_last_login=47.0,
            ml_anomaly_score=-0.30,
        )
        self.assertIn("geo_drift", login_score.triggered_rules)
        self.assertLess(login_score.trust_score, 80)


class TestModel(unittest.TestCase):
    def test_model_loads_and_scores(self):
        model = load_model()
        self.assertIsNotNone(model, "Expected backend/ml_model.pkl to exist and load")

        benign_vector = build_feature_vector(180, 45, 62, 1, 0.95, 88, 3)
        bot_vector = build_feature_vector(2, 1.1, 0, 14, 0.1, 44, 85)

        benign_score = predict(benign_vector, model)
        bot_score = predict(bot_vector, model)

        self.assertGreaterEqual(benign_score, -1.0)
        self.assertLessEqual(benign_score, 0.0)
        self.assertGreaterEqual(bot_score, -1.0)
        self.assertLessEqual(bot_score, 0.0)
        self.assertLess(bot_score, benign_score)


class TestLiveSmoke(unittest.TestCase):
    def test_backend_health_endpoint(self):
        if not _service_is_up(f"{BACKEND_BASE}/health"):
            self.skipTest(f"Backend not reachable at {BACKEND_BASE}")

        response = requests.get(f"{BACKEND_BASE}/health", timeout=5)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")

    def test_frontend_root_endpoint(self):
        if not _service_is_up(FRONTEND_BASE):
            self.skipTest(f"Frontend not reachable at {FRONTEND_BASE}")

        response = requests.get(FRONTEND_BASE, timeout=5)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<div id="root"></div>', response.text)

    def test_register_endpoint_smoke(self):
        if not _service_is_up(f"{BACKEND_BASE}/health"):
            self.skipTest(f"Backend not reachable at {BACKEND_BASE}")

        email = f"suite.{uuid.uuid4().hex[:12]}@example.com"
        response = requests.post(
            f"{API_BASE}/register",
            json={
                "email": email,
                "password": "Demo@12345",
                "behavioral": {
                    "typing_variance_ms": 180,
                    "time_to_complete_sec": 45,
                    "mouse_move_count": 55,
                    "keypress_count": 95,
                    "session_tempo_sec": 5.0,
                    "mouse_entropy_score": 0.8,
                    "fill_order_score": 0.95,
                },
            },
            headers={"X-Forwarded-For": "203.0.113.55", "User-Agent": "Mozilla/5.0"},
            timeout=10,
        )

        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIn("trust_score", data)
        self.assertIn("recommendation", data)


class TestSMTPHardening(unittest.TestCase):
    """Test SMTP delivery hardening and retry logic."""
    
    def test_mailer_imports(self):
        """Verify mailer module imports correctly."""
        sys.path.insert(0, str(BACKEND_DIR))
        try:
            from mailer import send_otp_email, smtp_is_configured
            self.assertIsNotNone(send_otp_email)
            self.assertIsNotNone(smtp_is_configured)
        except ImportError as e:
            self.fail(f"Failed to import mailer: {e}")
    
    def test_otp_session_has_delivery_status(self):
        """Verify OtpSession model has delivery tracking fields."""
        sys.path.insert(0, str(BACKEND_DIR))
        from models import OtpSession
        
        # Check that the model has the required columns
        columns = {col.name for col in OtpSession.__table__.columns}
        self.assertIn("delivery_status", columns, "OtpSession missing delivery_status column")
        self.assertIn("delivery_attempts", columns, "OtpSession missing delivery_attempts column")
        self.assertIn("last_delivery_error", columns, "OtpSession missing last_delivery_error column")
    
    def test_mailer_returns_structured_result(self):
        """Verify send_otp_email returns structured result dict."""
        sys.path.insert(0, str(BACKEND_DIR))
        from mailer import send_otp_email
        
        # Send OTP (will likely be not_configured or console_fallback if SMTP not set)
        result = send_otp_email("test@example.com", "123456")
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("status", result, "Missing 'status' in result")
        self.assertIn("attempts", result, "Missing 'attempts' in result")
        self.assertIn("error", result, "Missing 'error' in result")
        self.assertIn("timestamp", result, "Missing 'timestamp' in result")
        
        # Status must be one of the expected values
        valid_statuses = ["delivered", "failed", "console_fallback", "not_configured"]
        self.assertIn(result["status"], valid_statuses, f"Invalid status: {result['status']}")
    
    def test_smtp_env_vars_documented(self):
        """Verify SMTP env vars are documented in .env.example."""
        env_example = _read_text(".env.example")
        self.assertIn("SMTP_RETRIES", env_example)
        self.assertIn("SMTP_TIMEOUT", env_example)
        self.assertIn("SMTP_STRICT_MODE", env_example)


if __name__ == "__main__":
    unittest.main(verbosity=2)
