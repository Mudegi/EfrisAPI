# EFRIS API Error Documentation

This folder contains detailed error reports and suggested fixes for issues encountered while integrating with the EFRIS External API at `https://efrisintegration.nafacademy.com/api/external/efris`.

## Purpose

To provide the EFRIS development team with:
- Clear error descriptions
- Exact request/response details
- Root cause analysis
- Suggested fixes with code examples
- Testing instructions

## EFRIS API Endpoints Being Tested

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/submit-invoice` | POST | Fiscalize invoices and get FDN | ⏳ Testing |
| `/register-product` | POST | Register products in EFRIS | ⏳ Testing |
| `/submit-purchase-order` | POST | Add stock via bills/POs | ⏳ Testing |
| `/submit-credit-note` | POST | Issue credit memos | ⏳ Testing |
| `/excise-duty` | GET | Fetch excise duty codes | ✅ **FIXED** |
| `/stock-decrease` | POST | Reduce stock in EFRIS | ⏳ Testing |

## Error Reports

### Currently Documented Errors

1. **[ERROR-001: GET /excise-duty - AttributeError](./ERROR-001-excise-duty-attribute-error.md)**
   - Error: `'Company' object has no attribute 'is_test_mode'`
   - Status: ✅ **RESOLVED** (Feb 8, 2026)
   - Endpoint: GET /excise-duty
   - Severity: High (was blocking)
   - Fix: Changed `company.is_test_mode` to `company.efris_test_mode` in 6 endpoints

## How to Use This Documentation

### For YourBookSuit Developers
- Add new error files as you encounter them
- Follow the template format (see ERROR-001 as example)
- Update the status table above

### For EFRIS Support Team
- Each error file contains:
  - Complete error details
  - Request/response examples
  - Root cause analysis
  - Specific code fixes needed
  - Testing instructions
- Use these reports to quickly identify and fix backend issues

## Contact Information

**YourBookSuit Team:**
- Testing Organization: Demo Company Inc.
- Organization ID: cmkr0wbeq0001vl95dodsfurp
- API Key: (provided separately)
- Environment: Test Mode

**EFRIS Support:**
- Email: support@efrisintegration.com
- API Base URL: https://efrisintegration.nafacademy.com/api/external/efris

## Error Report Template

When creating new error reports, use this structure:

```markdown
# ERROR-XXX: [Endpoint] - [Brief Description]

## Error Summary
- **Endpoint:** [Full URL]
- **Method:** [GET/POST]
- **HTTP Status:** [500/400/etc]
- **Error Message:** [Exact error text]
- **Date Discovered:** [YYYY-MM-DD]
- **Severity:** [High/Medium/Low]

## Request Details
[Full request with headers, body, etc]

## Response Details
[Full error response]

## Root Cause Analysis
[What's wrong in the backend code]

## Suggested Fix
[Code examples showing what needs to be fixed]

## Testing Instructions
[How to verify the fix works]
```

---

**Last Updated:** February 8, 2026  
**Total Errors Documented:** 1  
**Errors Resolved:** 0
