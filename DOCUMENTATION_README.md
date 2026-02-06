# 📚 EFRIS Integration - Complete Documentation

Welcome to the EFRIS Integration API documentation suite! This collection provides everything you need to integrate your system with Uganda's EFRIS (Electronic Fiscal Receipting and Invoicing System).

---

## 🎯 Quick Navigation

| Document | Purpose | Audience |
|----------|---------|----------|
| [API Endpoints Guide](API_ENDPOINTS_GUIDE.md) | Complete API reference | Developers |
| [External API Documentation](EXTERNAL_API_DOCUMENTATION.md) | Integration overview | Technical Teams |
| [Custom ERP Integration Guide](CUSTOM_ERP_INTEGRATION_GUIDE.md) | Step-by-step integration | ERP Developers |
| [Troubleshooting FAQ](TROUBLESHOOTING_FAQ.md) | Common issues & solutions | All Users |
| [Video Tutorial Scripts](VIDEO_TUTORIAL_SCRIPTS.md) | Tutorial creation guide | Content Creators |
| [Postman Collection](EFRIS_API_Postman_Collection.json) | API testing & examples | Developers |

---

## 🚀 Getting Started (5 Minutes)

### 1. Get Your API Key

**Option A: Dashboard**
1. Login at https://efrisintegration.nafacademy.com
2. Navigate to **Settings → API Keys**
3. Click **Generate New Key**
4. Copy and save securely

**Option B: Contact Support**
- Email: support@efrisintegration.com
- WhatsApp: +256 XXX XXX XXX

### 2. Test the Connection

```bash
# Using cURL
curl -X GET "https://efrisintegration.nafacademy.com/api/external/efris/health" \
  -H "X-API-Key: efris_your_key_here"

# Expected response
{"status": "healthy", "version": "2.0.0"}
```

### 3. Submit Your First Invoice

```python
import requests

API_KEY = "efris_your_key_here"
BASE_URL = "https://efrisintegration.nafacademy.com/api/external/efris"

invoice = {
    "invoice_number": "INV-001",
    "invoice_date": "2026-02-06",
    "customer_name": "ABC Company Ltd",
    "customer_tin": "1000000000",
    "items": [{
        "description": "Laptop Computer",
        "quantity": 1,
        "unit_price": 2500000,
        "tax_rate": 18
    }]
}

response = requests.post(
    f"{BASE_URL}/submit-invoice",
    json=invoice,
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Success! FDN: {result['fdn']}")
    print(f"QR Code: {result['qr_code']}")
else:
    print(f"❌ Error: {response.json()['error']}")
```

### 4. View Interactive API Docs

Visit **https://efrisintegration.nafacademy.com/docs** for:
- ✅ Interactive Swagger UI
- ✅ Try API calls directly in browser
- ✅ Auto-generated request/response examples
- ✅ Authentication testing

Alternative: **https://efrisintegration.nafacademy.com/redoc** for ReDoc format

---

## 📖 Documentation Overview

### For Developers

<details>
<summary><b>🔧 Custom ERP Integration Guide</b> (Click to expand)</summary>

**File:** [CUSTOM_ERP_INTEGRATION_GUIDE.md](CUSTOM_ERP_INTEGRATION_GUIDE.md)

**Contents:**
- Quick Start (5-minute test)
- Authentication & security
- Complete API endpoints reference
- Integration patterns:
  - Real-time integration
  - Batch processing
  - Webhook notifications
- Code examples in:
  - Python (Django/Flask)
  - PHP (Laravel)
  - JavaScript (Node.js/Express)
  - C# (.NET)
- Error handling & retry logic
- Unit testing examples
- Production checklist

**Best for:** ERP developers integrating EFRIS into existing systems

</details>

<details>
<summary><b>📡 External API Documentation</b> (Click to expand)</summary>

**File:** [EXTERNAL_API_DOCUMENTATION.md](EXTERNAL_API_DOCUMENTATION.md)

**Contents:**
- Authentication methods
- All API endpoints with examples
- Request/response formats
- Common error codes
- Rate limiting information
- Best practices

**Best for:** General API reference

</details>

<details>
<summary><b>📮 Postman Collection</b> (Click to expand)</summary>

**File:** [EFRIS_API_Postman_Collection.json](EFRIS_API_Postman_Collection.json)

**How to use:**
1. Open Postman
2. Click **Import**
3. Select `EFRIS_API_Postman_Collection.json`
4. Set your API key in **Collection Variables**
5. Start testing!

**Includes:**
- ✅ 30+ pre-configured API requests
- ✅ Examples for all endpoints
- ✅ Error scenario testing
- ✅ Simple & complex invoice examples
- ✅ Product registration
- ✅ Webhook management

**Best for:** Quick API testing without writing code

</details>

### For End Users

<details>
<summary><b>❓ Troubleshooting FAQ</b> (Click to expand)</summary>

**File:** [TROUBLESHOOTING_FAQ.md](TROUBLESHOOTING_FAQ.md)

**Contents:**
- **Authentication Issues**
  - Invalid API key
  - Token expired
  - Cannot login
  
- **Invoice Submission Errors**
  - Error codes (100, 01, 02, etc.)
  - Duplicate invoice numbers
  - Invalid date format
  - Tax calculation errors
  
- **Product Registration Problems**
  - Product already exists
  - Invalid category codes
  
- **Network & Connection Issues**
  - Timeouts
  - SSL certificate errors
  
- **Certificate & Encryption Issues**
  - Failed to load certificate
  - Invalid signatures
  - AES encryption problems
  
- **Database Issues**
  - Database locked
  - Missing tables
  - Migration failures
  
- **Dashboard & UI Problems**
  - Dashboard not loading
  - Mobile issues
  
- **Performance Issues**
  - Slow API responses
  - EFRIS delays
  
- **Deployment Issues**
  - Deployment failures
  - Dependency problems

**Quick Diagnostic Checklist:**
```bash
# 1. Check API connection
curl https://efrisintegration.nafacademy.com/api/external/efris/health

# 2. Test authentication
curl -H "X-API-Key: your_key" https://efrisintegration.nafacademy.com/api/external/efris/health

# 3. Check certificate (if using local deployment)
ls -la *.p12

# 4. Verify database
sqlite3 efris_api.db ".tables"

# 5. Check logs
tail -f logs/efris_api.log

# 6. Test EFRIS connection
ping efrisws.ura.go.ug

# 7. Check Python version
python3 --version  # Should be 3.8+
```

**Best for:** Diagnosing and fixing common issues

</details>

<details>
<summary><b>🎥 Video Tutorial Scripts</b> (Click to expand)</summary>

**File:** [VIDEO_TUTORIAL_SCRIPTS.md](VIDEO_TUTORIAL_SCRIPTS.md)

**7 Complete Tutorial Scripts:**

1. **Getting Started - First Invoice** (10 min)
   - Login and dashboard tour
   - Creating your first invoice
   - Submitting to EFRIS
   - Understanding FDN and QR codes

2. **Setting Up API Integration** (8 min)
   - Generating API keys
   - Testing connection
   - Submitting via API
   - Error handling

3. **Product Registration** (5 min)
   - Adding products to catalog
   - Choosing EFRIS categories
   - Managing product library

4. **Handling Errors** (7 min)
   - Common error types
   - Debugging techniques
   - Solutions to typical problems

5. **Mobile Dashboard Setup** (6 min)
   - Installing PWA on mobile
   - Mobile invoice submission
   - Offline features

6. **Custom ERP Integration** (15 min)
   - Webhook setup
   - Real-time synchronization
   - Error recovery

7. **Excise Duty Invoices** (8 min)
   - Identifying excisable goods
   - Applying excise codes
   - Tax calculations

**Each script includes:**
- Scene-by-scene breakdown
- Timecodes for editing
- Narrator text (voiceover script)
- Screen actions (what to show)
- Graphics notes (annotations to add)

**Recording Tips Included:**
- Equipment needed
- Best practices
- Post-production guide
- YouTube publishing checklist

**Best for:** Creating consistent, professional video tutorials

</details>

---

## 📊 Feature Comparison

| Feature | Dashboard | API | Mobile App |
|---------|-----------|-----|------------|
| Submit Invoices | ✅ | ✅ | ✅ |
| Register Products | ✅ | ✅ | ✅ |
| View Statistics | ✅ | ✅ | ✅ |
| Download QR Codes | ✅ | ✅ | ✅ |
| Batch Operations | ❌ | ✅ | ❌ |
| Webhooks | ❌ | ✅ | ❌ |
| Offline Mode | ❌ | ❌ | ✅ |
| Print Receipts | ✅ | via API | ✅ |

---

## 🔌 Integration Approaches

### Option 1: Direct API Integration ⭐ Recommended

**Best for:** Custom ERP systems, automated workflows

```
Your ERP → HTTP API → EFRIS Integration → EFRIS
```

**Pros:**
- Full control over integration
- Real-time or batch processing
- Webhook support
- Error handling in your code

**Getting Started:** [Custom ERP Integration Guide](CUSTOM_ERP_INTEGRATION_GUIDE.md)

---

### Option 2: Dashboard Manual Entry

**Best for:** Small businesses, occasional invoices

```
User → Web Dashboard → EFRIS Integration → EFRIS
```

**Pros:**
- No coding required
- User-friendly interface
- Mobile-responsive
- Quick setup

**Getting Started:** Login at https://efrisintegration.nafacademy.com

---

### Option 3: Mobile App (PWA)

**Best for:** Field sales, on-the-go invoicing

```
User → Mobile PWA → EFRIS Integration → EFRIS
```

**Pros:**
- Works offline
- Install on any device
- Camera for barcode scanning
- Push notifications

**Getting Started:** Visit https://efrisintegration.nafacademy.com on mobile

---

### Option 4: Hybrid (API + Dashboard)

**Best for:** Medium businesses with mixed needs

```
ERP (bulk) → API → EFRIS Integration → EFRIS
Manual → Dashboard ↗
```

**Pros:**
- Flexibility
- Automated + manual workflows
- Best of both worlds

---

## 🛠️ API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check API status |
| `/submit-invoice` | POST | Submit invoice to EFRIS |
| `/register-product` | POST | Register product |
| `/query-invoice/{number}` | GET | Get invoice status |
| `/invoices` | GET | List invoices (paginated) |
| `/products` | GET | List products (paginated) |
| `/dashboard/stats` | GET | Get statistics |
| `/webhooks/subscribe` | POST | Subscribe to events |
| `/reference/product-categories` | GET | Get category codes |
| `/reference/payment-modes` | GET | Get payment codes |
| `/reference/excise-codes` | GET | Get excise duty codes |

**Full Reference:** [API Endpoints Guide](API_ENDPOINTS_GUIDE.md)

---

## 🔐 Authentication

All API requests require authentication via API key:

```http
X-API-Key: efris_your_api_key_here
```

**Security Best Practices:**
- ✅ Store API keys in environment variables
- ✅ Use HTTPS only
- ✅ Rotate keys every 90-365 days
- ✅ Never commit keys to version control
- ❌ Never hardcode keys in source code
- ❌ Never share keys via email/chat

---

## 📈 Rate Limits

| Tier | Requests/Min | Requests/Day |
|------|--------------|--------------|
| Free | 60 | 1,000 |
| Basic | 100 | 10,000 |
| Pro | 300 | 50,000 |
| Enterprise | Unlimited | Unlimited |

**Handling Rate Limits:**
```python
import time

def submit_with_retry(invoice_data):
    max_retries = 3
    for attempt in range(max_retries):
        response = submit_invoice(invoice_data)
        
        if response.status_code == 429:  # Too Many Requests
            wait_time = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
        elif response.status_code == 200:
            return response.json()
        else:
            break
    
    return None
```

---

## 🧪 Testing

### Postman Collection

1. Import [EFRIS_API_Postman_Collection.json](EFRIS_API_Postman_Collection.json)
2. Set variables:
   - `api_key`: Your API key
   - `base_url`: https://efrisintegration.nafacademy.com/api/external/efris
3. Run requests!

### Test Environment

```
Base URL: https://staging.efrisintegration.nafacademy.com/api/external/efris
Test TIN: 1000000000
Test Data: Safe to experiment
```

### Sample Test Script

```python
# test_efris_integration.py

def test_submit_invoice():
    invoice = {
        "invoice_number": f"TEST-{int(time.time())}",
        "invoice_date": datetime.now().strftime("%Y-%m-%d"),
        "customer_name": "Test Customer",
        "items": [{
            "description": "Test Product",
            "quantity": 1,
            "unit_price": 10000,
            "tax_rate": 18
        }]
    }
    
    result = efris.submit_invoice(invoice)
    
    assert result['success'] == True
    assert 'fdn' in result
    assert result['fdn'].startswith('1000000000')
    
    print("✅ Test passed!")

if __name__ == '__main__':
    test_submit_invoice()
```

---

## 🐛 Troubleshooting Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| "Invalid API Key" | Check key format, regenerate if needed |
| Connection timeout | Check internet, increase timeout to 30s |
| "Missing required field" | Review request format in docs |
| "Duplicate invoice" | Use unique invoice numbers with timestamp |
| SSL certificate error | Update certificates: `pip install --upgrade certifi` |
| Rate limit exceeded | Wait 60s and retry |
| Database locked | Check for concurrent access |

**Full Guide:** [Troubleshooting FAQ](TROUBLESHOOTING_FAQ.md)

---

## 📞 Support & Resources

### Documentation
- 📖 **API Docs:** https://efrisintegration.nafacademy.com/docs
- 📘 **ReDoc:** https://efrisintegration.nafacademy.com/redoc
- 💻 **GitHub:** [Repository link here]

### Contact Support
- 📧 **Email:** support@efrisintegration.com
- 💬 **WhatsApp:** +256 XXX XXX XXX
- 🌐 **Website:** https://efrisintegration.nafacademy.com
- 🔧 **Status Page:** https://status.efrisintegration.com

### Community
- 💡 **Feature Requests:** Open GitHub issue
- 🐛 **Bug Reports:** Email support with logs
- 📚 **Knowledge Base:** https://docs.efrisintegration.com

---

## 🎓 Learning Path

### Beginner
1. Read [Quick Start](#-getting-started-5-minutes)
2. Watch **Tutorial 1: Getting Started** (when available)
3. Submit test invoice via Dashboard
4. Review [Troubleshooting FAQ](TROUBLESHOOTING_FAQ.md)

### Intermediate
1. Read [External API Documentation](EXTERNAL_API_DOCUMENTATION.md)
2. Import [Postman Collection](EFRIS_API_Postman_Collection.json)
3. Submit invoice via API
4. Set up error logging

### Advanced
1. Read [Custom ERP Integration Guide](CUSTOM_ERP_INTEGRATION_GUIDE.md)
2. Implement retry logic
3. Set up webhooks
4. Add batch processing
5. Implement rate limiting

### Expert
1. Optimize performance (caching, bulk operations)
2. Set up monitoring & alerts
3. Implement advanced error recovery
4. Create custom dashboards
5. Contribute to documentation

---

## 🗺️ Roadmap

### Completed ✅
- Multi-tenant support
- API key authentication
- Invoice submission
- Product registration
- Dashboard & statistics
- Mobile PWA
- Comprehensive documentation
- Postman collection
- Video tutorial scripts

### In Progress 🚧
- Video tutorial recording
- Enhanced webhook system
- Advanced analytics
- Multi-language support

### Planned 📋
- Bulk import/export
- Advanced reporting
- Credit note support
- Integration marketplace
- Developer sandbox
- SDKs (Python, PHP, Node.js)

---

## 📄 License & Terms

- **API Usage:** Subject to terms of service
- **Rate Limits:** Based on subscription tier
- **Support:** Email/WhatsApp during business hours
- **SLA:** 99.9% uptime guarantee (Pro/Enterprise)

---

## 🙏 Acknowledgments

Built with:
- FastAPI (Python web framework)
- SQLite (Database)
- Uvicorn (ASGI server)
- GitHub Actions (CI/CD)

Special thanks to all contributors and early adopters!

---

## 📝 Document Change Log

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | 2026-02-06 | Complete documentation overhaul |
| 1.5.0 | 2026-02-01 | Added video tutorial scripts |
| 1.4.0 | 2026-01-28 | Added Postman collection |
| 1.3.0 | 2026-01-25 | Enhanced troubleshooting guide |
| 1.2.0 | 2026-01-20 | Added ERP integration examples |
| 1.1.0 | 2026-01-15 | Initial external API docs |
| 1.0.0 | 2026-01-10 | First release |

---

**📌 Last Updated:** February 6, 2026  
**📌 Version:** 2.0.0  
**📌 Maintained by:** EFRIS Integration Team

---

**Need help?** Start with the [Troubleshooting FAQ](TROUBLESHOOTING_FAQ.md) or contact support!

**Ready to integrate?** Jump to the [Custom ERP Integration Guide](CUSTOM_ERP_INTEGRATION_GUIDE.md)!

**Just testing?** Import the [Postman Collection](EFRIS_API_Postman_Collection.json) and start exploring!
