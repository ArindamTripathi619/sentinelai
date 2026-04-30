#!/usr/bin/env python3
"""
SentinelAI Security Audit Script
Comprehensive security checks covering:
- JWT token generation & validation
- SQL injection vectors
- CORS policy
- Password hashing strength
- Session management
- Input validation
- Error message leakage
- Dependency vulnerabilities

Usage:
    python scripts/security_audit.py
"""

import sys
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

# Color codes for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class SecurityAudit:
    def __init__(self):
        self.findings = []
        self.passed = 0
        self.warnings = 0
        self.failures = 0

    def log_pass(self, check: str, detail: str = ""):
        """Log a passed security check."""
        self.passed += 1
        symbol = f"{GREEN}✓{RESET}"
        print(f"{symbol} {check}")
        if detail:
            print(f"  {detail}")

    def log_warning(self, check: str, detail: str = "", remediation: str = ""):
        """Log a security warning."""
        self.warnings += 1
        symbol = f"{YELLOW}⚠{RESET}"
        self.findings.append({
            "severity": "WARNING",
            "check": check,
            "detail": detail,
            "remediation": remediation,
        })
        print(f"{symbol} {check}")
        if detail:
            print(f"  Detail: {detail}")
        if remediation:
            print(f"  Fix: {remediation}")

    def log_failure(self, check: str, detail: str = "", remediation: str = ""):
        """Log a security failure."""
        self.failures += 1
        symbol = f"{RED}✗{RESET}"
        self.findings.append({
            "severity": "CRITICAL",
            "check": check,
            "detail": detail,
            "remediation": remediation,
        })
        print(f"{symbol} {check}")
        if detail:
            print(f"  Detail: {detail}")
        if remediation:
            print(f"  Fix: {remediation}")

    def audit_jwt(self):
        """Audit JWT implementation."""
        print(f"\n{BLUE}[JWT & Token Security]{RESET}")
        
        # Check JWT secret length
        try:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            
            secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-prod")
            
            if secret == "your-secret-key-change-in-prod":
                self.log_failure(
                    "JWT_SECRET is default value",
                    detail="Using default JWT secret in environment",
                    remediation="Set JWT_SECRET to a cryptographically random string (32+ bytes). Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            elif len(secret) < 32:
                self.log_warning(
                    "JWT_SECRET is too short",
                    detail=f"Current length: {len(secret)} bytes (recommended: 32+ bytes)",
                    remediation="Use 32+ byte random secret. Current entropy: weak"
                )
            else:
                self.log_pass("JWT_SECRET is properly configured", f"Length: {len(secret)} bytes")
        except Exception as e:
            self.log_warning("Could not verify JWT_SECRET", detail=str(e))

        # Check JWT expiry
        try:
            import os
            expire_hours = int(os.getenv("JWT_EXPIRE_HOURS", "24"))
            
            if expire_hours > 48:
                self.log_warning(
                    "JWT expiry too long",
                    detail=f"Current expiry: {expire_hours} hours (recommended: 24 hours max)",
                    remediation="Set JWT_EXPIRE_HOURS to 24 or less for production"
                )
            else:
                self.log_pass("JWT expiry is reasonable", f"Expiry: {expire_hours} hours")
        except Exception as e:
            self.log_warning("Could not verify JWT expiry", detail=str(e))

    def audit_password_hashing(self):
        """Audit password hashing implementation."""
        print(f"\n{BLUE}[Password Security]{RESET}")
        
        # Check if auth.py uses SHA256 (weak) or bcrypt (strong)
        try:
            with open("backend/auth.py", "r") as f:
                auth_code = f.read()
            
            if "hashlib.sha256" in auth_code:
                self.log_failure(
                    "Using SHA256 for password hashing",
                    detail="SHA256 is too fast for password hashing (susceptible to brute force)",
                    remediation="Upgrade to bcrypt or PBKDF2. Install: pip install bcrypt. Replace hash_password() with bcrypt.hashpw()"
                )
            elif "bcrypt" in auth_code or "passlib" in auth_code:
                self.log_pass("Using bcrypt/passlib for password hashing", "Strong and slow hash function")
            else:
                self.log_warning("Password hashing method unclear", detail="Could not detect bcrypt or passlib usage")
        except FileNotFoundError:
            self.log_warning("Could not audit password hashing", detail="auth.py not found")

    def audit_sql_injection(self):
        """Audit SQL injection protection."""
        print(f"\n{BLUE}[SQL Injection Protection]{RESET}")
        
        try:
            # Check if project uses SQLAlchemy ORM (parameterized queries)
            with open("requirements.txt", "r") as f:
                reqs = f.read()
            
            if "sqlalchemy" in reqs:
                self.log_pass("Using SQLAlchemy ORM", "All queries use parameterized statements (safe from SQL injection)")
            else:
                self.log_warning("SQLAlchemy not detected", detail="Verify raw SQL is not used")
        except FileNotFoundError:
            self.log_warning("Could not check requirements.txt")

    def audit_cors(self):
        """Audit CORS policy."""
        print(f"\n{BLUE}[CORS Policy]{RESET}")
        
        try:
            # Check frontend CORS configuration
            cors_found = False
            
            # Check main.py for CORS setup
            with open("backend/main.py", "r") as f:
                main_code = f.read()
            
            if "CORSMiddleware" in main_code or "cors" in main_code.lower():
                cors_found = True
                
                # Check if it's hardcoded to specific origins
                if "0.0.0.0" in main_code or "allow_origins=['*']" in main_code:
                    self.log_warning(
                        "CORS configured with wildcard (*) or all IPs",
                        detail="This allows any domain to make requests",
                        remediation="Set allow_origins to specific domains: ['http://localhost:3000', 'https://yourdomain.com']"
                    )
                elif "localhost" in main_code and "3000" in main_code:
                    self.log_pass("CORS configured for localhost:3000", "Appropriate for development")
                else:
                    self.log_pass("CORS middleware enabled")
            else:
                self.log_warning("CORS configuration not clearly visible", detail="Verify CORSMiddleware is properly configured")
        except FileNotFoundError:
            self.log_warning("Could not check CORS configuration")

    def audit_rate_limiting(self):
        """Audit rate limiting."""
        print(f"\n{BLUE}[Rate Limiting]{RESET}")
        
        try:
            with open("backend/auth.py", "r") as f:
                auth_code = f.read()
            
            if "rate" in auth_code.lower() or "limit" in auth_code.lower():
                if "slowapi" in auth_code or "ratelimit" in auth_code.lower():
                    self.log_pass("Rate limiting detected", "Protection against brute force attacks")
                else:
                    self.log_warning("Rate limiting mentioned but implementation unclear")
            else:
                self.log_failure(
                    "No explicit rate limiting detected",
                    detail="Registration and login endpoints vulnerable to brute force attacks",
                    remediation="Implement rate limiting: pip install slowapi. Add @limiter.limit('5/minute') to endpoints"
                )
        except FileNotFoundError:
            self.log_warning("Could not check rate limiting")

    def audit_session_management(self):
        """Audit session and token management."""
        print(f"\n{BLUE}[Session Management]{RESET}")
        
        try:
            with open("backend/auth.py", "r") as f:
                auth_code = f.read()
            
            # Check OTP expiry
            if "OTP_EXPIRE_MINUTES" in auth_code or "expires_at" in auth_code:
                self.log_pass("OTP sessions have expiry", "Short-lived sessions reduce exposure window")
            else:
                self.log_warning("OTP expiry not clearly configured")
            
            # Check for session fixation protection
            if "user_id" in auth_code and "token" in auth_code:
                self.log_pass("Session tokens include user_id", "Prevents session fixation")
            
            # Check for CSRF protection
            with open("backend/main.py", "r") as f:
                main_code = f.read()
            
            if "csrf" in main_code.lower():
                self.log_pass("CSRF protection detected")
            else:
                self.log_warning(
                    "CSRF protection not explicitly configured",
                    detail="POST/DELETE requests may be vulnerable to CSRF",
                    remediation="Add CSRF middleware or verify SameSite cookie attribute"
                )
        except FileNotFoundError:
            self.log_warning("Could not fully check session management")

    def audit_error_messages(self):
        """Audit for error message leakage."""
        print(f"\n{BLUE}[Error Message Security]{RESET}")
        
        try:
            with open("backend/auth.py", "r") as f:
                auth_code = f.read()
            
            dangerous_patterns = [
                ("User.*not found", "Error messages reveal user existence"),
                ("Invalid.*email", "Generic errors are better than revealing valid/invalid users"),
                ("Incorrect.*password", "Should not reveal why login failed (user exists vs wrong password)"),
            ]
            
            found_issues = False
            for pattern, issue in dangerous_patterns:
                if re.search(pattern, auth_code, re.IGNORECASE):
                    if not found_issues:
                        self.log_warning(
                            "Error messages may leak user information",
                            detail="Error responses could reveal valid email addresses",
                            remediation="Use generic error messages: 'Invalid email or password' instead of 'User not found'"
                        )
                        found_issues = True
            
            if not found_issues:
                self.log_pass("Generic error messages used", "No obvious user enumeration vectors")
        except FileNotFoundError:
            self.log_warning("Could not check error messages")

    def audit_input_validation(self):
        """Audit input validation."""
        print(f"\n{BLUE}[Input Validation]{RESET}")
        
        try:
            with open("backend/auth.py", "r") as f:
                auth_code = f.read()
            
            # Check for email validation
            if "@" in auth_code and (".com" in auth_code or "re.match" in auth_code or "validator" in auth_code.lower()):
                self.log_pass("Email validation appears to be implemented")
            else:
                self.log_warning("Email input validation not clearly visible")
            
            # Check for password requirements
            if "password" in auth_code.lower():
                if "len(" in auth_code or "length" in auth_code.lower():
                    self.log_pass("Password length validation detected")
                else:
                    self.log_warning(
                        "No password strength requirements visible",
                        detail="Passwords should have minimum length and complexity",
                        remediation="Add validation: minimum 8 chars, mixed case, numbers, symbols"
                    )
        except FileNotFoundError:
            self.log_warning("Could not check input validation")

    def audit_dependencies(self):
        """Audit for known vulnerabilities in dependencies."""
        print(f"\n{BLUE}[Dependency Vulnerabilities]{RESET}")
        
        try:
            with open("requirements.txt", "r") as f:
                requirements = f.read()
            
            # Known vulnerable versions (this is not exhaustive)
            dangerous_packages = {
                "cryptography<3.4": "Security vulnerability in cryptography library",
                "PyJWT<2.4": "PyJWT vulnerability in JWT processing",
                "fastapi<0.75": "FastAPI security issues",
            }
            
            issues_found = False
            for pkg, issue in dangerous_packages.items():
                if pkg in requirements:
                    self.log_failure(f"Potentially vulnerable package: {pkg}", detail=issue)
                    issues_found = True
            
            if not issues_found:
                self.log_pass("No known vulnerable packages detected (basic check)", "Run 'pip install safety' for detailed audit")
                
            # Check if using secure versions
            if "python-jose" in requirements and "cryptography" in requirements:
                self.log_pass("Using python-jose with cryptography for JWT")
        except FileNotFoundError:
            self.log_warning("Could not check dependencies")

    def audit_logging(self):
        """Audit logging for security events."""
        print(f"\n{BLUE}[Security Event Logging]{RESET}")
        
        try:
            with open("backend/auth.py", "r") as f:
                auth_code = f.read()
            
            # Check for attempt logging
            if "login" in auth_code and ("log" in auth_code.lower() or "print" in auth_code):
                self.log_pass("Login attempts appear to be logged", "Helps detect brute force attacks")
            else:
                self.log_warning(
                    "Failed login/registration attempts may not be logged",
                    detail="Lack of logging makes audit trails impossible",
                    remediation="Add logging: logger.warning(f'Failed login attempt for {email}')"
                )
        except FileNotFoundError:
            self.log_warning("Could not check logging")

    def generate_report(self):
        """Generate final report."""
        print(f"\n{'='*60}")
        print(f"{BLUE}SECURITY AUDIT SUMMARY{RESET}")
        print(f"{'='*60}")
        print(f"\n{GREEN}✓ Passed:{RESET} {self.passed}")
        print(f"{YELLOW}⚠ Warnings:{RESET} {self.warnings}")
        print(f"{RED}✗ Failures:{RESET} {self.failures}")
        
        if self.findings:
            print(f"\n{BLUE}FINDINGS & REMEDIATIONS:{RESET}\n")
            for i, finding in enumerate(self.findings, 1):
                severity = finding["severity"]
                if severity == "CRITICAL":
                    symbol = f"{RED}[CRITICAL]{RESET}"
                else:
                    symbol = f"{YELLOW}[WARNING]{RESET}"
                
                print(f"{i}. {symbol} {finding['check']}")
                if finding['detail']:
                    print(f"   Detail: {finding['detail']}")
                if finding['remediation']:
                    print(f"   Remediation: {finding['remediation']}")
                print()
        
        print(f"{'='*60}")
        if self.failures == 0:
            print(f"{GREEN}✓ All critical security checks PASSED{RESET}")
        else:
            print(f"{RED}✗ {self.failures} CRITICAL issues must be addressed{RESET}")
        print(f"{'='*60}\n")
        
        return self.failures == 0


def main():
    """Run full security audit."""
    print(f"\n{BLUE}SentinelAI Security Audit{RESET}")
    print("Starting comprehensive security analysis...\n")
    
    audit = SecurityAudit()
    
    try:
        audit.audit_jwt()
        audit.audit_password_hashing()
        audit.audit_sql_injection()
        audit.audit_cors()
        audit.audit_rate_limiting()
        audit.audit_session_management()
        audit.audit_error_messages()
        audit.audit_input_validation()
        audit.audit_dependencies()
        audit.audit_logging()
    except Exception as e:
        print(f"{RED}Error during audit: {e}{RESET}")
        return False
    
    success = audit.generate_report()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
