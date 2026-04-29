# SentinelAI — Security Rules Engine
# Owner: Akash
# Each rule returns a penalty (int) and optionally creates an alert.
# All rules are independent — they don't call each other.

from dataclasses import dataclass, field
from typing import List, Optional
import re

# Disposable email domains to flag
DISPOSABLE_DOMAINS = {
    "temp.com", "mailinator.com", "guerrillamail.com",
    "throwam.com", "fakeinbox.com", "trashmail.com",
    "yopmail.com", "getairmail.com", "dispostable.com"
}


@dataclass
class RuleResult:
    rule_name: str
    triggered: bool
    penalty: int
    alert_type: Optional[str] = None
    alert_severity: Optional[str] = None
    alert_description: Optional[str] = None


@dataclass
class RulesEngineOutput:
    total_penalty: int = 0
    triggered_rules: List[str] = field(default_factory=list)
    alerts_to_create: List[RuleResult] = field(default_factory=list)


def check_velocity_ip(ip_address: str, registrations_from_ip_last_hour: int) -> RuleResult:
    """
    Rule: More than 3 registrations from the same IP in the last hour → bot wave.
    Penalty: 25 points
    """
    # TODO: Akash implements this
    # Query the DB for how many registrations came from this IP in the last 60 minutes
    # For now, accept the count as a parameter (Atul's endpoint will compute it)
    limit = 3
    triggered = registrations_from_ip_last_hour > limit
    return RuleResult(
        rule_name="velocity_ip",
        triggered=triggered,
        penalty=25 if triggered else 0,
        alert_type="bot_wave" if triggered else None,
        alert_severity="critical" if triggered else None,
        alert_description=(
            f"IP {ip_address} made {registrations_from_ip_last_hour} registrations in the last hour"
            if triggered else None
        )
    )


def check_email_pattern(email: str) -> RuleResult:
    """
    Rule: Sequential email names (user1, user2...) or disposable domains → flag.
    Penalty: 20 points
    """
    # TODO: Akash implements this
    domain = email.split("@")[-1].lower()
    local = email.split("@")[0].lower()

    is_disposable = domain in DISPOSABLE_DOMAINS
    is_sequential = bool(re.match(r'^(user|test|temp|fake|bot)\d+$', local))

    triggered = is_disposable or is_sequential
    return RuleResult(
        rule_name="email_pattern",
        triggered=triggered,
        penalty=20 if triggered else 0,
    )


def check_speed_bot(time_to_complete_sec: float, min_seconds: float = 4.0) -> RuleResult:
    """
    Rule: Registration completed faster than minimum human time → speed bot.
    Penalty: 20 points
    """
    # TODO: Akash implements this
    triggered = time_to_complete_sec < min_seconds
    return RuleResult(
        rule_name="speed_bot",
        triggered=triggered,
        penalty=20 if triggered else 0,
        alert_type="speed_bot" if triggered else None,
        alert_severity="high" if triggered else None,
        alert_description=(
            f"Registration completed in {time_to_complete_sec:.1f}s (threshold: {min_seconds}s)"
            if triggered else None
        )
    )


def check_duplicate_device(user_agent: str, accounts_with_same_ua_today: int) -> RuleResult:
    """
    Rule: Same user-agent string on 3+ different accounts in 24h → shared bot device.
    Penalty: 15 points
    """
    # TODO: Akash implements this
    triggered = accounts_with_same_ua_today >= 3
    return RuleResult(
        rule_name="duplicate_device",
        triggered=triggered,
        penalty=15 if triggered else 0,
    )


def check_geo_drift(
    user_id: str,
    current_country: str,
    last_country: Optional[str],
    minutes_since_last_login: Optional[float]
) -> RuleResult:
    """
    Rule: Same account logs in from different country within 2 hours → session hijack / drift.
    Penalty: 30 points (applied to login, not registration)
    """
    # TODO: Akash implements this
    if last_country is None or minutes_since_last_login is None:
        return RuleResult(rule_name="geo_drift", triggered=False, penalty=0)

    triggered = (current_country != last_country) and (minutes_since_last_login < 120)
    return RuleResult(
        rule_name="geo_drift",
        triggered=triggered,
        penalty=30 if triggered else 0,
        alert_type="geo_drift" if triggered else None,
        alert_severity="high" if triggered else None,
        alert_description=(
            f"User {user_id} logged in from {last_country} then {current_country} "
            f"within {minutes_since_last_login:.0f} minutes"
            if triggered else None
        )
    )


def run_registration_rules(
    email: str,
    time_to_complete_sec: float,
    ip_address: str,
    user_agent: str,
    registrations_from_ip_last_hour: int,
    accounts_with_same_ua_today: int,
) -> RulesEngineOutput:
    """
    Run all registration-time rules and aggregate the output.
    Called by the /api/register endpoint (via scorer.py).
    """
    results = [
        check_velocity_ip(ip_address, registrations_from_ip_last_hour),
        check_email_pattern(email),
        check_speed_bot(time_to_complete_sec),
        check_duplicate_device(user_agent, accounts_with_same_ua_today),
    ]

    output = RulesEngineOutput()
    for r in results:
        if r.triggered:
            output.total_penalty += r.penalty
            output.triggered_rules.append(r.rule_name)
            if r.alert_type:
                output.alerts_to_create.append(r)

    return output


def run_login_rules(
    user_id: str,
    ip_address: str,
    current_country: str,
    last_country: Optional[str],
    minutes_since_last_login: Optional[float],
) -> RulesEngineOutput:
    """
    Run all login-time rules (currently just geo drift).
    """
    results = [
        check_geo_drift(user_id, current_country, last_country, minutes_since_last_login),
    ]

    output = RulesEngineOutput()
    for r in results:
        if r.triggered:
            output.total_penalty += r.penalty
            output.triggered_rules.append(r.rule_name)
            if r.alert_type:
                output.alerts_to_create.append(r)

    return output
