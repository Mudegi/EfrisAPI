# 🔐 EFRIS Security Features - Client Briefing Guide

## Overview
This document explains the security features implemented in your EFRIS Integration Portal and provides guidance on how to brief your clients about these protections.

---

## Table of Contents
1. [Login Process](#login-process)
2. [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa)
3. [Additional Security Features](#additional-security-features)
4. [Client Briefing Scripts](#client-briefing-scripts)
5. [Real-World Protection Scenarios](#real-world-protection-scenarios)
6. [Client FAQ](#client-faq)
7. [Technical Details](#technical-details)

---

## Login Process

### Standard Login (Without 2FA)

**Steps:**
1. Navigate to your portal URL (e.g., `http://yourcompany.com/owner`)
2. Enter email address
3. Enter password
4. Click "Login as Owner"
5. Dashboard loads immediately

**Security Level:** 🟡 Basic (password-only protection)

---

### Enhanced Login (With 2FA Enabled)

**Initial Setup (One-Time, 5 minutes):**
1. Log into your Owner Portal using email/password
2. Navigate to **🔐 Security tab** in the dashboard
3. Click **"Enable 2FA"** button
4. System generates a unique QR code specific to your account
5. Install authenticator app on your smartphone:
   - **Google Authenticator** (free, iOS/Android)
   - **Microsoft Authenticator** (free, iOS/Android)
   - **Authy** (free, iOS/Android, with cloud backup)
6. Open authenticator app and scan the QR code displayed
7. App generates a 6-digit code
8. Enter the code to verify and activate 2FA
9. ✅ 2FA is now enabled on your account

**Daily Login Process (adds ~10 seconds):**
1. Navigate to portal URL
2. Enter email and password (as usual)
3. **NEW STEP:** Open authenticator app on your phone
4. Read the current 6-digit code (changes every 30 seconds)
5. Enter the 6-digit code in the "2FA Code" field
6. Click "Login as Owner"
7. ✅ Access granted

**Security Level:** 🟢 Bank-Level (password + physical device required)

---

## Two-Factor Authentication (2FA)

### What is 2FA?

Two-Factor Authentication requires **two separate forms of identification**:
1. **Something you know** - Your password
2. **Something you have** - Your phone (physical device)

Even if someone steals your password, they cannot access your account without also having your phone in their hand at that exact moment.

### How It Works Technically

**Technology:** TOTP (Time-based One-Time Password) - RFC 6238 standard
- Same technology used by Google, Microsoft, GitHub, and major banks

**The Process:**
1. During setup, system generates a unique "secret key" for your account
2. This secret is stored securely in the database and in your phone's authenticator app
3. Both your phone and our server use this secret + current time to generate codes
4. Code changes every 30 seconds
5. Server accepts codes with ±90 second window (allows for slight clock drift)
6. Each code can only be used once

**Why This Is Secure:**
- Codes are **never transmitted** before login
- Codes **expire** in 30 seconds
- Codes are **generated offline** on your phone (no internet needed)
- Even if someone intercepts a code, it's useless after 30 seconds

---

## Additional Security Features

### 1. IP Whitelisting (For Custom ERP API Access)

**What It Does:**
- Restricts API access to specific IP addresses or networks
- Blocks all other locations automatically

**Use Case:**
- Client has office at fixed IP: `203.45.67.89`
- You whitelist only that IP
- API calls from anywhere else are blocked with `403 Forbidden`

**Configuration:**
- Security tab → Client Security Settings → 🌐 IP Whitelist
- Supports wildcards: `192.168.1.*` (allows entire subnet)
- Empty whitelist = allow all (for flexibility)

### 2. API Rate Limiting

**What It Does:**
- Limits the number of API requests per client per day
- Default: 1,000 requests/day
- Configurable: 100 - 100,000 requests/day
- Resets daily at midnight

**Protection Against:**
- Data scraping attacks
- Accidental loops in client code
- Deliberate abuse/overuse

**Configuration:**
- Security tab → Client Security Settings → ⚡ Rate Limit
- If client hits limit: Returns `429 Too Many Requests`
- Headers show remaining quota: `X-RateLimit-Remaining: 847`

### 3. Security Audit Logs

**What It Tracks:**
- All login attempts (successful and failed)
- 2FA setup/enable/disable events
- IP whitelist changes
- Rate limit updates
- Rate limit violations
- Blocked IP addresses

**Information Logged:**
- Timestamp (when it happened)
- Action type (what happened)
- User email (who did it)
- Company name (which client)
- Details (additional context)

**Access:**
- Security tab → Security Audit Logs
- Filter by action type
- Export to CSV for compliance/reporting

---

## Client Briefing Scripts

### For Clients Who Ask "Why Do I Need 2FA?"

> **Your Message:**
> 
> "Your EFRIS system handles sensitive tax data, invoices, and financial records worth thousands or millions of shillings. We've implemented bank-level security that requires your phone as a second key to access your account.
> 
> Even if someone steals your password through phishing, keyloggers, or a data breach, they cannot access your account without physically having your phone in their hand. This is the same security standard used by Google, Microsoft, and international banks to protect billions of users worldwide.
> 
> It's a small time investment - just 10 extra seconds per login - that prevents devastating security incidents that could cost your business its reputation and expose you to legal liability."

---

### For Clients Worried About Complexity

> **Your Message:**
> 
> "I understand you want to keep things simple. Here's the reality:
> 
> **Setup:** 5 minutes, one time only
> **Daily use:** Adds just 10 seconds to your login
> 
> **The process:**
> 1. Enter your password (exactly as before)
> 2. Open your phone's authenticator app
> 3. Type the 6-digit number you see
> 4. Done
> 
> After 2-3 logins, it becomes automatic - like entering your PIN at an ATM. You do it without thinking.
> 
> And here's what you get: Protection that blocks 99.9% of password-based attacks. No more worrying about whether your password was leaked in a data breach."

---

### For Clients Who Travel or Work Remotely

> **Your Message:**
> 
> "This is **especially** important for you because you:
> - Log in from hotels, cafes, airports with public WiFi
> - Access your account from multiple locations
> - May have employees accessing the system remotely
> 
> Public WiFi networks are often monitored by hackers. Even with HTTPS encryption, sophisticated attacks can capture passwords. With 2FA enabled:
> 
> ✅ Hacker intercepts your password over hotel WiFi
> ✅ They try to log in from another country
> ✅ System asks for 6-digit code from YOUR phone
> ✅ They don't have your phone → BLOCKED immediately
> ✅ You see the failed attempt in our audit logs
> ✅ Your data remains 100% secure
> 
> Without 2FA, that scenario ends with a data breach."

---

### For Clients Managing Multiple Employees

> **Your Message:**
> 
> "With multiple people accessing your system, 2FA provides accountability and security:
> 
> **Security Benefits:**
> - Each employee has unique 2FA on their own phone
> - Cannot share login credentials (requires their specific phone)
> - If employee leaves: Disable their account, they lose access immediately
> - Audit logs show exactly who logged in when
> 
> **Real Scenario:**
> - Employee laptop gets stolen at coffee shop
> - Laptop has password saved in browser
> - Thief tries to log in → System asks for 6-digit code from employee's phone
> - Thief doesn't have phone → Access denied
> - Your business data stays protected
> 
> **Without 2FA:** That stolen laptop = full access to your financial data."

---

## Real-World Protection Scenarios

### Scenario 1: Employee Laptop Stolen

**Without 2FA:**
```
1. Laptop stolen from employee's car
2. Password saved in browser (auto-fill enabled)
3. Thief opens browser → Auto-logs into EFRIS portal
4. Full access to:
   - All customer invoices
   - Tax identification numbers
   - Banking details
   - URA tax submissions
5. Thief creates fraudulent invoices
6. Your company liable for fake tax records
7. URA audit reveals discrepancies
8. Legal consequences + reputation damage
```

**With 2FA:**
```
1. Laptop stolen from employee's car
2. Password saved in browser
3. Thief opens browser → Enters password successfully
4. System presents: "Enter 6-digit code from your authenticator"
5. Thief doesn't have employee's phone → BLOCKED 🚫
6. Failed login attempt logged in audit trail
7. You see alert: "Failed login from unknown location"
8. You remotely disable employee's account
9. Zero data compromised ✅
10. You issue employee new credentials on their new laptop
```

---

### Scenario 2: Phishing Email Attack

**Attacker sends email:**
```
Subject: URGENT: Your EFRIS Account Suspended!
From: ura-support@efris-verify.com (fake domain)

Your EFRIS account will be suspended in 24 hours.
Click here to verify: http://fake-efris-login.com
```

**Without 2FA:**
```
1. Employee clicks link (fake website looks identical to real one)
2. Employee enters email and password
3. Attacker captures credentials in real-time
4. Attacker logs into your REAL account within minutes
5. Downloads all customer data, invoices, tax records
6. Potentially modifies records or creates fake invoices
7. You discover breach weeks later from URA audit
```

**With 2FA:**
```
1. Employee clicks link and enters password (still bad)
2. Attacker captures password
3. Attacker tries to log into REAL account
4. System asks for 6-digit 2FA code
5. Attacker doesn't have employee's phone
6. Code changes every 30 seconds (even if they trick employee)
7. BLOCKED 🚫
8. Failed login attempt appears in audit logs
9. You identify compromised employee
10. You force password reset
11. Zero data lost ✅
```

---

### Scenario 3: Password Reuse / Data Breach at Another Company

**The Problem:**
- Average person reuses same password across 3-5 websites
- LinkedIn, Facebook, Yahoo, etc. have all been breached
- Hackers compile lists of millions of email/password combinations
- They try these credentials on every major platform

**Without 2FA:**
```
1. Employee uses same password on LinkedIn and EFRIS
2. LinkedIn gets hacked → 700 million passwords leaked
3. Hackers try leaked passwords on every business platform
4. Your employee's password works on your EFRIS account
5. Hackers access your tax data from another country
6. You discover breach from URA notification weeks later
```

**With 2FA:**
```
1. Employee uses same password on LinkedIn and EFRIS (still bad practice)
2. LinkedIn gets hacked → Password leaked
3. Hackers try password on your EFRIS account
4. Password works BUT system asks for 6-digit code
5. Hackers don't have employee's physical phone
6. BLOCKED 🚫 immediately
7. Failed login attempt logged
8. You see alert: "Login attempt from Russia" (example)
9. You notify employee to change password
10. Account remains secure ✅
```

---

### Scenario 4: Insider Threat / Disgruntled Employee

**Without 2FA:**
```
1. Employee decides to leave company
2. Before leaving, they copy all customer data
3. They remember login credentials
4. After leaving, they log in remotely from home
5. Download more sensitive data or create fake records
6. Difficult to prove who did it (shared passwords)
```

**With 2FA:**
```
1. Employee decides to leave company
2. You disable their account immediately
3. Their 2FA is tied to their phone (you don't have their device)
4. Even if they know password, they can't log in
5. Audit logs show last access was before termination
6. Clean separation, zero unauthorized access ✅
```

---

## Client FAQ

### Setup & Usage

**Q: How long does 2FA setup take?**
A: 5 minutes for first-time setup. After that, adds only 10 seconds per login.

**Q: What if I lose my phone?**
A: Contact us immediately at [your support email]. We can:
- Verify your identity through backup security questions
- Temporarily disable 2FA
- Help you set up 2FA on your new phone
- Re-enable 2FA once configured

**Q: Does the authenticator app require internet?**
A: **No!** The app works completely offline. It uses your phone's internal clock to generate codes. No cellular data or WiFi needed.

**Q: What if the code doesn't work when I enter it?**
A: Two possible causes:
1. **Code expired** - Codes change every 30 seconds. Get a fresh code and enter it quickly.
2. **Phone clock wrong** - Ensure your phone's date/time is set to automatic.
   
We allow a 90-second window, so minor time differences are okay.

**Q: Can I use the same authenticator app for multiple accounts?**
A: **Yes!** One app can store codes for unlimited accounts:
- Your EFRIS account
- Gmail
- Microsoft 365
- Facebook
- Banking apps
- etc.

Each account shows separately in the app with its own 6-digit code.

---

### Security Concerns

**Q: What if someone steals both my phone AND laptop?**
A: 
- Your phone should have a lock screen (PIN/fingerprint/face ID)
- Thief needs to unlock your phone to see authenticator codes
- You should report phone stolen and wipe it remotely
- We can disable your EFRIS account until you recover access
- You can set up 2FA again on a new phone

**Q: Is 2FA mandatory for all users?**
A: 
- **Owner/Admin accounts:** Strongly recommended (handles sensitive operations)
- **Regular employees:** Optional but encouraged
- **You decide** based on your security requirements

**Q: Can someone bypass 2FA?**
A: Extremely difficult. They would need:
1. Your password (something you know)
2. Physical access to your unlocked phone (something you have)
3. Or access to your backup recovery codes

This is why 2FA blocks 99.9% of attacks - it's exponentially harder than stealing just a password.

**Q: What happens if I enter the wrong 2FA code?**
A: 
- Login is denied
- Event is logged in security audit trail
- You can try again with the current code
- After multiple failed attempts, account may be temporarily locked for security

---

### Technical Questions

**Q: How secure is this compared to SMS codes?**
A: **Much more secure!**
- SMS codes can be intercepted (SIM swapping attacks)
- Authenticator app codes are generated on-device (offline)
- No transmission that can be intercepted
- Industry standard: Same tech used by Google, Microsoft, banks

**Q: How is the 6-digit code generated?**
A: 
- Uses TOTP (Time-based One-Time Password) standard (RFC 6238)
- Combines your unique secret key + current timestamp
- Results in a unique code every 30 seconds
- Server does same calculation and compares results
- Mathematical impossibility to predict next code without the secret

**Q: Where is my 2FA secret stored?**
A: 
- Encrypted in our database
- Also stored in your authenticator app (encrypted on device)
- Never transmitted over internet after initial setup
- Cannot be viewed by anyone after setup (not even admins)

**Q: What if our internet goes down?**
A: 
- **Authenticator app works offline** (on your phone)
- **Server validation requires internet** (on our side)
- If your office internet is down, you cannot log in from office
- But you CAN log in from mobile data or another location

---

### Business Continuity

**Q: What if your support team isn't available when I need 2FA reset?**
A: We recommend:
1. Set up 2FA for multiple administrators (backup)
2. Save backup recovery codes in secure location
3. Store emergency contact information with your IT team
4. We provide 24/7 emergency support for account lockouts

**Q: Can we disable 2FA for urgent access?**
A: Yes, but requires:
- Owner/administrator approval
- Identity verification (multiple factors)
- Temporary access with forced re-enable after emergency
- Full audit trail of the exception

**Q: What about new employees?**
A: Simple process:
1. You create their account (owner portal)
2. They log in first time with temporary password
3. System prompts them to set up 2FA (if required)
4. Takes 5 minutes, one-time setup
5. They're secured from day one

---

## Technical Details (For IT Teams)

### 2FA Implementation

**Technology Stack:**
- **Library:** pyotp (Python TOTP implementation)
- **Standard:** RFC 6238 (Time-based One-Time Password)
- **Algorithm:** HMAC-SHA1
- **Code Length:** 6 digits
- **Time Step:** 30 seconds
- **Validation Window:** ±1 step (90 seconds total)

**Database Schema:**
```sql
users table:
  - totp_secret (VARCHAR 255, nullable, encrypted)
  - totp_enabled (BOOLEAN, default false)
```

**Security Features:**
- Secrets generated with cryptographically secure random (32 bytes)
- Base32 encoding for QR code compatibility
- Audit logging for all 2FA events
- Password required to disable 2FA
- Role-based access (owner/admin only)

**QR Code Generation:**
```
Format: otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}
Issuer: "EFRIS API"
Encoding: Base64 PNG image
```

---

### IP Whitelisting Implementation

**How It Works:**
- Stored as JSON array in `companies.allowed_ips` column
- Checked on every API request (Custom ERP endpoints only)
- Supports exact match: `203.45.67.89`
- Supports wildcards: `192.168.1.*` or `10.0.*.*`
- Empty/null = allow all IPs (backward compatible)

**IP Detection Order:**
1. `X-Forwarded-For` header (for proxies/load balancers)
2. `X-Real-IP` header (for Nginx/reverse proxies)
3. Direct connection IP

**Enforcement:**
- Returns `403 Forbidden` if IP not whitelisted
- Logs blocked attempts to audit log
- Headers include rate limit info

---

### Rate Limiting Implementation

**How It Works:**
- Stored in `companies` table:
  - `api_rate_limit` (INTEGER, default 1000) - max requests/day
  - `api_calls_today` (INTEGER, default 0) - current count
  - `api_last_reset` (TIMESTAMP) - last reset time
  
**Reset Logic:**
- Automatic daily reset at midnight (server timezone)
- Resets counter to 0
- Updates `api_last_reset` timestamp

**Enforcement:**
- Checked on every Custom ERP API request
- Increments counter after validation
- Returns `429 Too Many Requests` if exceeded
- Response headers:
  - `X-RateLimit-Limit: 1000`
  - `X-RateLimit-Remaining: 847`
  - `X-RateLimit-Reset: 2026-02-07T00:00:00Z`

---

### Security Audit Log

**Logged Events:**
- `login` - Successful login
- `2fa_enabled` - 2FA activated on account
- `2fa_disabled` - 2FA removed from account
- `2fa_failed` - Invalid 2FA code entered
- `ip_whitelist_updated` - IP whitelist modified
- `rate_limit_updated` - Rate limit changed
- `rate_limit_exceeded` - Client hit daily limit
- `ip_blocked` - Request from non-whitelisted IP
- `API_KEY_REGENERATED` - API credentials refreshed

**Log Schema:**
```sql
audit_logs table:
  - id (INTEGER, primary key)
  - company_id (INTEGER, nullable, foreign key)
  - user_id (INTEGER, nullable, foreign key)
  - action (VARCHAR, indexed)
  - details (TEXT, JSON format)
  - created_at (TIMESTAMP)
```

**Retention:**
- Unlimited (no automatic deletion)
- Export available via UI (CSV format)
- Filter by action, company, date range

---

### API Endpoints

**2FA Management:**
```
POST /api/auth/2fa/setup          - Generate QR code
POST /api/auth/2fa/enable         - Activate 2FA (requires code verification)
POST /api/auth/2fa/disable        - Deactivate 2FA (requires password)
POST /api/auth/login?totp_code=   - Login with 2FA code
```

**Security Management (Owner Only):**
```
PUT /api/owner/clients/{id}/ip-whitelist   - Update IP whitelist (JSON array)
PUT /api/owner/clients/{id}/rate-limit     - Update rate limit (integer)
GET /api/owner/audit-logs                  - View security events (filterable)
```

---

## Summary

✅ **Implemented Security Features:**
- ✅ Two-Factor Authentication (TOTP-based)
- ✅ IP Whitelisting (with wildcard support)
- ✅ API Rate Limiting (configurable per client)
- ✅ Comprehensive Audit Logging
- ✅ Secure session management
- ✅ Role-based access control

✅ **Protection Against:**
- ✅ Password theft/leaks
- ✅ Phishing attacks
- ✅ Brute force attacks
- ✅ Data scraping
- ✅ Unauthorized API access
- ✅ Insider threats
- ✅ Remote attacks

✅ **Compliance Benefits:**
- ✅ Full audit trail for security events
- ✅ Industry-standard authentication
- ✅ Data protection best practices
- ✅ URA compliance ready

---

## Next Steps for Clients

1. **Immediate:** Enable 2FA on all owner/admin accounts
2. **Within 1 week:** Train employees on 2FA usage
3. **Within 1 month:** Enable 2FA for all users handling sensitive data
4. **Ongoing:** Review security audit logs monthly
5. **Quarterly:** Audit IP whitelists and rate limits

---

## Support Contact

For questions about security features:
- **Email:** [Your support email]
- **Phone:** [Your support phone]
- **Hours:** [Your support hours]
- **Emergency:** [24/7 contact for account lockouts]

---

**Document Version:** 1.0  
**Last Updated:** February 6, 2026  
**Applies to:** EFRIS Integration Portal v2.0+
