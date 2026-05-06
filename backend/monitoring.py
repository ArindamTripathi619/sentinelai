"""
Monitoring and metrics for SentinelAI.
Provides Prometheus metrics, performance tracking, and event alerting.
"""

from prometheus_client import Counter, Histogram, Gauge
import time
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# === COUNTERS ===
# Track occurrences of events

# Authentication metrics
auth_registration_total = Counter(
    'sentinelai_auth_registration_total',
    'Total registration attempts',
    ['status']  # success, rate_limited, blocked
)

auth_login_total = Counter(
    'sentinelai_auth_login_total',
    'Total login attempts',
    ['status']  # success, failed, otp_required, quarantined
)

auth_otp_sent_total = Counter(
    'sentinelai_auth_otp_sent_total',
    'Total OTP codes sent',
    ['status']  # delivered, failed, console_fallback
)

auth_token_validation_failures = Counter(
    'sentinelai_auth_token_validation_failures_total',
    'Total JWT token validation failures',
    ['reason']  # expired, invalid, malformed
)

# Security metrics
security_rules_triggered = Counter(
    'sentinelai_security_rules_triggered_total',
    'Total security rules fired',
    ['rule_name']  # velocity_ip, email_pattern, geo_drift, etc.
)

security_alerts_created = Counter(
    'sentinelai_security_alerts_created_total',
    'Total security alerts created',
    ['alert_type']  # bot_wave, geo_drift, suspicious_behavior
)

api_requests_total = Counter(
    'sentinelai_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_errors_total = Counter(
    'sentinelai_api_errors_total',
    'Total API errors',
    ['endpoint', 'error_code']
)

# === HISTOGRAMS ===
# Track request latency and durations

api_request_duration = Histogram(
    'sentinelai_api_request_duration_seconds',
    'API request latency in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

auth_registration_duration = Histogram(
    'sentinelai_auth_registration_duration_seconds',
    'Registration request duration in seconds',
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
)

password_hash_duration = Histogram(
    'sentinelai_password_hash_duration_seconds',
    'Password hashing duration in seconds',
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0)
)

db_query_duration = Histogram(
    'sentinelai_db_query_duration_seconds',
    'Database query latency in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5)
)

# === GAUGES ===
# Track current state (values that go up and down)

active_users_online = Gauge(
    'sentinelai_active_users_online',
    'Currently active users (estimate based on recent activity)'
)

users_in_quarantine = Gauge(
    'sentinelai_users_in_quarantine',
    'Number of users currently in quarantine'
)

trust_score_average = Gauge(
    'sentinelai_trust_score_average',
    'Average trust score across all users'
)

rate_limit_remaining = Gauge(
    'sentinelai_rate_limit_remaining',
    'Remaining rate limit capacity (per endpoint)',
    ['endpoint']
)


# === ALERT THRESHOLDS ===

class AlertThreshold:
    """Alert configuration and state."""
    
    # Failed auth attempts per minute to trigger alert
    FAILED_LOGIN_ATTEMPTS_THRESHOLD = 10
    
    # Bot wave detection: registrations per minute
    BOT_WAVE_REGISTRATIONS_THRESHOLD = 5
    
    # Geo drift detections per minute to escalate
    GEO_DRIFT_ALERTS_THRESHOLD = 3
    
    # API error rate (percentage) to trigger alert
    API_ERROR_RATE_THRESHOLD = 5  # %
    
    # Database query latency to trigger alert (seconds)
    DB_QUERY_LATENCY_THRESHOLD = 1.0


class MetricsCollector:
    """Centralized metrics collection and alerting."""
    
    def __init__(self):
        self.alert_callbacks = []
        self.event_log = []
    
    def register_alert_callback(self, callback):
        """Register a callback to be called when an alert is triggered."""
        self.alert_callbacks.append(callback)
    
    def log_event(self, event_type: str, severity: str, message: str, context: dict = None):
        """Log an event for alerting and auditing."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'severity': severity,  # info, warning, critical
            'message': message,
            'context': context or {},
        }
        self.event_log.append(event)
        
        # Trigger alert callbacks if critical
        if severity == 'critical':
            self._trigger_alert(event)
        
        logger.warning(
            f"[ALERT] {event_type} - {message}",
            extra={'severity': severity, 'context': context}
        )
    
    def _trigger_alert(self, event: dict):
        """Execute alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")
    
    def check_failed_login_spike(self, failed_count: int):
        """Check if failed login attempts exceed threshold."""
        if failed_count > AlertThreshold.FAILED_LOGIN_ATTEMPTS_THRESHOLD:
            self.log_event(
                'AUTH_SPIKE',
                'critical',
                f'High failed login rate: {failed_count} in last minute',
                {'threshold': AlertThreshold.FAILED_LOGIN_ATTEMPTS_THRESHOLD}
            )
            return True
        return False
    
    def check_bot_wave(self, registration_count: int):
        """Check if registrations per minute indicate bot wave."""
        if registration_count > AlertThreshold.BOT_WAVE_REGISTRATIONS_THRESHOLD:
            self.log_event(
                'BOT_WAVE',
                'critical',
                f'Bot wave detected: {registration_count} registrations in last minute',
                {'threshold': AlertThreshold.BOT_WAVE_REGISTRATIONS_THRESHOLD}
            )
            return True
        return False
    
    def check_geo_drift_spike(self, geo_drift_count: int):
        """Check for unusual geo drift patterns."""
        if geo_drift_count > AlertThreshold.GEO_DRIFT_ALERTS_THRESHOLD:
            self.log_event(
                'GEO_DRIFT_SPIKE',
                'warning',
                f'Multiple geo drift alerts: {geo_drift_count} in last minute',
                {'threshold': AlertThreshold.GEO_DRIFT_ALERTS_THRESHOLD}
            )
            return True
        return False


# Global metrics collector instance
metrics = MetricsCollector()


def record_request_timing(method: str, endpoint: str, duration: float, status_code: int):
    """Record API request metrics."""
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()


def record_error(endpoint: str, error_code: str):
    """Record API error."""
    api_errors_total.labels(endpoint=endpoint, error_code=error_code).inc()


def record_auth_event(event_type: str, status: str):
    """Record authentication event."""
    if event_type == 'registration':
        auth_registration_total.labels(status=status).inc()
    elif event_type == 'login':
        auth_login_total.labels(status=status).inc()


def record_security_rule(rule_name: str):
    """Record a security rule being triggered."""
    security_rules_triggered.labels(rule_name=rule_name).inc()


def record_alert(alert_type: str):
    """Record a security alert being created."""
    security_alerts_created.labels(alert_type=alert_type).inc()
