"""
SECURITY IMPLEMENTATION GUIDE

This file documents all security enhancements added to the EFRIS platform.
Use this as reference when integrating into api_multitenant.py

============================================================
STEP 1: ADD IMPORTS AT TOP OF api_multitenant.py
============================================================

Add after existing imports:
```python
from security_utils import (
    generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp_code,
    get_client_ip, enforce_api_security
)
```

============================================================
STEP 2: UPDATE get_company_from_api_key FUNCTION (Line ~85)
============================================================

Replace the function with this enhanced version:

```python
def get_company_from_api_key(
    request: Request,  # ADD THIS
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Company:
    '''Authenticate external ERP systems with IP whitelist & rate limiting'''
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    company = db.query(Company).filter(
        Company.api_key == x_api_key,
        Company.api_enabled == True,
        Company.is_active == True
    ).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or API access disabled",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # SECURITY CHECKS: IP Whitelisting + Rate Limiting
    enforce_api_security(request, company, db)
    
    return company
```

============================================================  
STEP 3: UPDATE LOGIN TO SUPPORT 2FA (Line ~946)
============================================================

Replace login function with 2FA check:

```python
@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: str = Form(None),  # ADD THIS - optional 2FA code
    db: Session = Depends(get_db)
):
    '''Login with optional 2FA verification'''
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # 2FA CHECK for owner/admin accounts
    if user.totp_enabled and user.role in ['owner', 'admin']:
        if not totp_code:
            raise HTTPException(
                status_code=403,
                detail="2FA code required",
                headers={"X-2FA-Required": "true"}
            )
        
        if not verify_totp_code(user.totp_secret, totp_code):
            # Log failed attempt
            audit_log = AuditLog(
                user_id=user.id,
                action="2fa_failed",
                details=f"Invalid 2FA code for {user.email}",
                ip_address="login"
            )
            db.add(audit_log)
            db.commit()
            
            raise HTTPException(
                status_code=403,
                detail="Invalid 2FA code"
            )
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }
```

============================================================
STEP 4: ADD NEW 2FA ENDPOINTS (Add after login endpoint)
============================================================

```python
@app.post("/api/auth/2fa/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    '''Generate 2FA secret and QR code for owner/admin'''
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="2FA only for owner/admin accounts")
    
    if current_user.totp_enabled:
        return {"message": "2FA already enabled", "enabled": True}
    
    # Generate new secret
    secret = generate_totp_secret()
    uri = get_totp_uri(current_user.email, secret)
    qr_code = generate_qr_code(uri)
    
    # Save secret (not enabled yet - user must verify first)
    current_user.totp_secret = secret
    db.commit()
    
    # Log setup
    audit_log = AuditLog(
        user_id=current_user.id,
        action="2fa_setup_initiated",
        details=f"2FA setup started for {current_user.email}",
        ip_address="system"
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_code}",
        "manual_entry": secret,
        "message": "Scan QR code with Google Authenticator or enter secret manually"
    }


@app.post("/api/auth/2fa/enable")
async def enable_2fa(
    code: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    '''Enable 2FA after verifying TOTP code'''
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not set up. Call /setup first")
    
    if not verify_totp_code(current_user.totp_secret, code):
        raise HTTPException(status_code=400, detail="Invalid verification code")
    
    current_user.totp_enabled = True
    db.commit()
    
    # Log activation
    audit_log = AuditLog(
        user_id=current_user.id,
        action="2fa_enabled",
        details=f"2FA enabled for {current_user.email}",
        ip_address="system"
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "message": "2FA enabled successfully"}


@app.post("/api/auth/2fa/disable")
async def disable_2fa(
    password: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    '''Disable 2FA (requires password confirmation)'''
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    
    # Log deactivation
    audit_log = AuditLog(
        user_id=current_user.id,
        action="2fa_disabled",
        details=f"2FA disabled for {current_user.email}",
        ip_address="system"
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "message": "2FA disabled"}
```

============================================================
STEP 5: ADD IP WHITELIST MANAGEMENT ENDPOINTS
============================================================

```python
@app.put("/api/owner/clients/{company_id}/ip-whitelist")
async def update_ip_whitelist(
    company_id: int,
    ips: list = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    '''Update IP whitelist for company API access'''
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Owner only")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    import json
    company.allowed_ips = json.dumps(ips)
    db.commit()
    
    # Log change
    audit_log = AuditLog(
        company_id=company.id,
        user_id=current_user.id,
        action="ip_whitelist_updated",
        details=f"IP whitelist updated: {ips}",
        ip_address="owner_portal"
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "allowed_ips": ips}


@app.put("/api/owner/clients/{company_id}/rate-limit")
async def update_rate_limit(
    company_id: int,
    limit: int = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    '''Update API rate limit for company'''
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Owner only")
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    company.api_rate_limit = limit
    db.commit()
    
    # Log change
    audit_log = AuditLog(
        company_id=company.id,
        user_id=current_user.id,
        action="rate_limit_updated",
        details=f"Rate limit updated to {limit} req/day",
        ip_address="owner_portal"
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "rate_limit": limit}
```

========================================================
STEP 6: ADD AUDIT LOG VIEWER ENDPOINT
========================================================

```python
@app.get("/api/owner/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    company_id: int = None,
    action_filter: str = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    '''Get security audit logs'''
    if current_user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Owner only")
    
    query = db.query(AuditLog)
    
    if company_id:
        query = query.filter(AuditLog.company_id == company_id)
    
    if action_filter:
        query = query.filter(AuditLog.action.like(f"%{action_filter}%"))
    
    logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "company_id": log.company_id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address
            }
            for log in logs
        ],
        "total": len(logs)
    }
```

=========================================================
ALL IMPLEMENTATION STEPS COMPLETE
=========================================================

After adding all endpoints above, restart server and test:

1. 2FA Setup: POST /api/auth/2fa/setup
2. IP Whitelist: PUT /api/owner/clients/{id}/ip-whitelist
3. Rate Limit: PUT /api/owner/clients/{id}/rate-limit  
4. Audit Logs: GET /api/owner/audit-logs
5. External API now enforces IP + rate limiting automatically

"""
