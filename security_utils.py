"""
Security Utilities for EFRIS Multi-Tenant Platform
- Two-Factor Authentication (2FA) using TOTP
- IP Whitelisting for Custom ERP API
- API Rate Limiting per client
"""
import pyotp
import qrcode
import io
import base64
import json
from datetime import datetime, date
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from database.models import Company, AuditLog


# ========== 2FA / TOTP Functions ==========

def generate_totp_secret():
    """Generate a new TOTP secret for 2FA"""
    return pyotp.random_base32()


def get_totp_uri(email: str, secret: str, issuer_name: str = "EFRIS Platform"):
    """Generate TOTP provisioning URI for QR code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer_name)


def generate_qr_code(uri: str) -> str:
    """Generate QR code image as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code. Window allows for time drift (default ±30 seconds)"""
    if not secret or not code:
        return False
    
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=window)


def get_current_totp_code(secret: str) -> str:
    """Get current TOTP code (for testing/debugging only)"""
    totp = pyotp.TOTP(secret)
    return totp.now()


# ========== IP Whitelisting Functions ==========

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP if multiple
        return forwarded.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return "unknown"


def parse_allowed_ips(allowed_ips_json: str) -> list:
    """Parse JSON string of allowed IPs"""
    if not allowed_ips_json:
        return []
    
    try:
        ips = json.loads(allowed_ips_json)
        return ips if isinstance(ips, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def is_ip_allowed(client_ip: str, allowed_ips: list) -> bool:
    """Check if client IP is in whitelist. Empty whitelist = allow all"""
    if not allowed_ips:
        # No whitelist = allow everyone
        return True
    
    # Check for exact match
    if client_ip in allowed_ips:
        return True
    
    # Check for wildcard patterns (e.g., "192.168.1.*")
    for allowed_pattern in allowed_ips:
        if "*" in allowed_pattern:
            pattern_parts = allowed_pattern.split(".")
            ip_parts = client_ip.split(".")
            
            if len(pattern_parts) == len(ip_parts):
                match = True
                for i, part in enumerate(pattern_parts):
                    if part != "*" and part != ip_parts[i]:
                        match = False
                        break
                
                if match:
                    return True
    
    return False


def check_ip_whitelist(request: Request, company: Company) -> bool:
    """Check if request IP is whitelisted for company"""
    client_ip = get_client_ip(request)
    allowed_ips = parse_allowed_ips(company.allowed_ips)
    
    is_allowed = is_ip_allowed(client_ip, allowed_ips)
    
    if not is_allowed:
        # Log failed attempt
        print(f"[Security] IP {client_ip} blocked for company {company.name} (TIN: {company.tin})")
    
    return is_allowed


# ========== API Rate Limiting Functions ==========

def reset_daily_counter_if_needed(company: Company, db: Session):
    """Reset API call counter if it's a new day"""
    now = datetime.now()
    today = date.today()
    
    # Check if we need to reset (new day or never reset)
    if not company.api_last_reset or company.api_last_reset.date() < today:
        company.api_calls_today = 0
        company.api_last_reset = now
        db.commit()


def check_rate_limit(company: Company, db: Session) -> tuple[bool, int, int]:
    """
    Check if company has exceeded rate limit
    Returns: (is_allowed, calls_remaining, limit)
    """
    # Reset counter if needed
    reset_daily_counter_if_needed(company, db)
    
    # Check limit
    limit = company.api_rate_limit or 1000
    calls_today = company.api_calls_today or 0
    
    is_allowed = calls_today < limit
    calls_remaining = max(0, limit - calls_today)
    
    return is_allowed, calls_remaining, limit


def increment_api_call_counter(company: Company, db: Session):
    """Increment API call counter for rate limiting"""
    reset_daily_counter_if_needed(company, db)
    
    company.api_calls_today = (company.api_calls_today or 0) + 1
    company.api_last_used = datetime.now()
    db.commit()


def log_rate_limit_exceeded(company: Company, client_ip: str, db: Session):
    """Log rate limit violation to audit log"""
    audit_log = AuditLog(
        company_id=company.id,
        user_id=None,  # External API, no user
        action="rate_limit_exceeded",
        details=f"API rate limit exceeded ({company.api_calls_today}/{company.api_rate_limit}). IP: {client_ip}",
        ip_address=client_ip
    )
    db.add(audit_log)
    db.commit()


# ========== Combined Security Check for External API ==========

def enforce_api_security(request: Request, company: Company, db: Session):
    """
    Comprehensive security check for external API endpoints
    - IP Whitelisting
    - Rate Limiting
    - Audit Logging
    
    Raises HTTPException if security check fails
    """
    client_ip = get_client_ip(request)
    
    # 1. Check IP Whitelist
    if not check_ip_whitelist(request, company):
        # Log security violation
        audit_log = AuditLog(
            company_id=company.id,
            user_id=None,
            action="ip_blocked",
            details=f"Blocked API request from non-whitelisted IP: {client_ip}",
            ip_address=client_ip
        )
        db.add(audit_log)
        db.commit()
        
        raise HTTPException(
            status_code=403,
            detail="Access denied: IP address not whitelisted for this API key"
        )
    
    # 2. Check Rate Limit
    is_allowed, calls_remaining, limit = check_rate_limit(company, db)
    
    if not is_allowed:
        log_rate_limit_exceeded(company, client_ip, db)
        
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Limit: {limit} requests/day. Try again tomorrow.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": company.api_last_reset.isoformat() if company.api_last_reset else ""
            }
        )
    
    # 3. Increment counter (passed all checks)
    increment_api_call_counter(company, db)
    
    # 4. Add rate limit headers to response (informational)
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(calls_remaining - 1),  # -1 because we just incremented
        "X-RateLimit-Reset": company.api_last_reset.isoformat() if company.api_last_reset else ""
    }
