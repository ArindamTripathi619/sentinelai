"""
Centralized error code definitions for SentinelAI.
Provides structured error responses for API consumers.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(str, Enum):
    """Standard error codes for SentinelAI API."""
    
    # Auth errors (1000-1099)
    AUTH_INVALID_CREDENTIALS = "ERR_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "ERR_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "ERR_TOKEN_INVALID"
    AUTH_UNAUTHORIZED = "ERR_UNAUTHORIZED"
    AUTH_USER_NOT_FOUND = "ERR_USER_NOT_FOUND"
    AUTH_USER_BLOCKED = "ERR_USER_BLOCKED"
    AUTH_USER_QUARANTINED = "ERR_USER_QUARANTINED"
    AUTH_OTP_INVALID = "ERR_OTP_INVALID"
    AUTH_OTP_EXPIRED = "ERR_OTP_EXPIRED"
    AUTH_OTP_NOT_SENT = "ERR_OTP_NOT_SENT"
    
    AUTH_RESET_TOKEN_INVALID = "ERR_RESET_TOKEN_INVALID"
    AUTH_RESET_TOKEN_EXPIRED = "ERR_RESET_TOKEN_EXPIRED"

    # Registration errors (1100-1199)
    REG_EMAIL_EXISTS = "ERR_EMAIL_EXISTS"
    REG_INVALID_EMAIL = "ERR_INVALID_EMAIL"
    REG_WEAK_PASSWORD = "ERR_WEAK_PASSWORD"
    REG_RATE_LIMIT = "ERR_REGISTRATION_RATE_LIMIT"
    REG_SUSPICIOUS_ACTIVITY = "ERR_REGISTRATION_SUSPICIOUS"
    
    # Validation errors (1200-1299)
    VAL_INVALID_REQUEST = "ERR_INVALID_REQUEST"
    VAL_MISSING_FIELD = "ERR_MISSING_FIELD"
    VAL_INVALID_FORMAT = "ERR_INVALID_FORMAT"
    
    # Database errors (1300-1399)
    DB_CONNECTION_FAILED = "ERR_DB_CONNECTION_FAILED"
    DB_QUERY_FAILED = "ERR_DB_QUERY_FAILED"
    DB_NOT_FOUND = "ERR_NOT_FOUND"
    
    # Security errors (1400-1499)
    SEC_RATE_LIMIT = "ERR_RATE_LIMIT_EXCEEDED"
    SEC_SUSPICIOUS_PATTERN = "ERR_SUSPICIOUS_PATTERN"
    SEC_GEO_DRIFT = "ERR_GEO_DRIFT_DETECTED"
    SEC_ANOMALY_DETECTED = "ERR_ANOMALY_DETECTED"
    
    # Service errors (1500-1599)
    SVC_INTERNAL_ERROR = "ERR_INTERNAL_ERROR"
    SVC_SERVICE_UNAVAILABLE = "ERR_SERVICE_UNAVAILABLE"
    SVC_TIMEOUT = "ERR_TIMEOUT"
    
    # External service errors (1600-1699)
    EXT_SMTP_FAILED = "ERR_SMTP_FAILED"
    EXT_GEO_LOOKUP_FAILED = "ERR_GEO_LOOKUP_FAILED"


class APIError(Exception):
    """Base API error with structured error response."""
    
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize structured API error.
        
        Args:
            code: ErrorCode enum value
            message: Human-readable error message
            status_code: HTTP status code
            details: Optional dict with additional error context
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert error to API response dict."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            }
        }


# Convenience subclasses for common errors

class AuthenticationError(APIError):
    """Authentication/authorization error (401)."""
    def __init__(
        self,
        code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS,
        message: str = "Invalid credentials",
        details: Optional[Dict] = None,
    ):
        super().__init__(code, message, status_code=401, details=details)


class ValidationError(APIError):
    """Input validation error (400)."""
    def __init__(
        self,
        code: ErrorCode = ErrorCode.VAL_INVALID_REQUEST,
        message: str = "Invalid request",
        details: Optional[Dict] = None,
    ):
        super().__init__(code, message, status_code=400, details=details)


class RateLimitError(APIError):
    """Rate limit exceeded error (429)."""
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict] = None,
    ):
        super().__init__(
            ErrorCode.SEC_RATE_LIMIT,
            message,
            status_code=429,
            details=details,
        )


class NotFoundError(APIError):
    """Resource not found error (404)."""
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict] = None,
    ):
        super().__init__(
            ErrorCode.DB_NOT_FOUND,
            message,
            status_code=404,
            details=details,
        )


class InternalError(APIError):
    """Internal server error (500)."""
    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict] = None,
    ):
        super().__init__(
            ErrorCode.SVC_INTERNAL_ERROR,
            message,
            status_code=500,
            details=details,
        )
