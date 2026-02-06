# 🔧 Custom ERP Integration - Developer Guide

Complete guide for integrating your ERP system with EFRIS API.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints Reference](#api-endpoints-reference)
4. [Integration Patterns](#integration-patterns)
5. [Code Examples](#code-examples)
6. [Webhooks](#webhooks)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Production Checklist](#production-checklist)

---

## 🚀 Quick Start

### Prerequisites

```bash
# Your ERP system should have:
✅ HTTP client library
✅ JSON parsing capability
✅ Secure API key storage
✅ Error logging system
```

### 5-Minute Integration Test

```python
# test_integration.py
import requests

API_KEY = "efris_your_key_here"
BASE_URL = "https://efrisintegration.nafacademy.com/api/external/efris"

# Test 1: Connection
response = requests.get(
    f"{BASE_URL}/health",
    headers={"X-API-Key": API_KEY}
)
print(f"✅ Connection: {response.status_code == 200}")

# Test 2: Submit Invoice
invoice = {
    "invoice_number": "TEST-001",
    "invoice_date": "2026-02-06",
    "customer_name": "Test Customer",
    "items": [{
        "description": "Test Product",
        "quantity": 1,
        "unit_price": 10000,
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
    print(f"✅ Invoice submitted: {response.json()['fdn']}")
else:
    print(f"❌ Error: {response.json()}")
```

---

## 🔐 Authentication

### API Key Generation

1. **Dashboard Method**:
   - Login → Settings → API Keys → Generate New Key
   - Copy and store securely

2. **Programmatic Method** (admin only):
   ```python
   POST /api/admin/generate-api-key
   {
       "company_id": 123,
       "description": "ERP Integration",
       "expires_in_days": 365
   }
   ```

### Using API Keys

**Header Format**:
```http
X-API-Key: efris_abc123def456...
Content-Type: application/json
```

**Example**:
```python
headers = {
    "X-API-Key": os.getenv("EFRIS_API_KEY"),
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers)
```

### Security Best Practices

```python
# ✅ DO: Use environment variables
API_KEY = os.getenv("EFRIS_API_KEY")

# ✅ DO: Rotate keys periodically
# Set expiration: 90-365 days

# ❌ DON'T: Hardcode keys
API_KEY = "efris_abc123..."  # NEVER!

# ❌ DON'T: Commit to version control
# Add to .gitignore: .env, config.ini

# ✅ DO: Use secrets management
# AWS Secrets Manager, Azure Key Vault, etc.
```

---

## 📡 API Endpoints Reference

### Base URL

```
Production: https://efrisintegration.nafacademy.com/api/external/efris
Staging: https://staging.efrisintegration.nafacademy.com/api/external/efris
```

### Endpoint Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/submit-invoice` | POST | Submit invoice to EFRIS |
| `/register-product` | POST | Register product with EFRIS |
| `/query-invoice` | GET | Get invoice status |
| `/invoices` | GET | List all invoices |
| `/products` | GET | List registered products |
| `/health` | GET | Check API status |

---

### 1. Submit Invoice

**Endpoint**: `POST /api/external/efris/submit-invoice`

**Request**:
```json
{
  "invoice_number": "INV-2026-001",
  "invoice_date": "2026-02-06",
  "customer_name": "ABC Company Ltd",
  "customer_tin": "1000000000",
  "customer_phone": "0700123456",
  "customer_email": "customer@abc.com",
  "customer_address": "Kampala, Uganda",
  "items": [
    {
      "description": "Laptop Computer",
      "item_code": "LAP-001",
      "quantity": 2,
      "unit_price": 2500000,
      "tax_rate": 18,
      "discount": 100000
    }
  ],
  "payment_mode": "101",
  "currency": "UGX"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "fdn": "1000000000-ABC-12345678",
  "qr_code": "https://efris.ura.go.ug/verify/...",
  "verification_code": "123456",
  "invoice_id": "uuid-here",
  "submitted_at": "2026-02-06T14:30:00Z"
}
```

**Response (Error)**:
```json
{
  "success": false,
  "error": "Missing required field: customer_tin",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "customer_tin",
    "required": true
  }
}
```

**Code Example**:
```python
def submit_invoice_to_efris(invoice_data):
    """Submit invoice from ERP to EFRIS"""
    
    url = f"{BASE_URL}/submit-invoice"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url,
            json=invoice_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Store FDN in your ERP
            save_fdn_to_erp(
                invoice_data['invoice_number'],
                result['fdn'],
                result['qr_code']
            )
            return result
        else:
            # Log error
            log_error(f"EFRIS error: {response.json()}")
            return None
            
    except requests.Timeout:
        log_error("EFRIS timeout - retry later")
        return None
    except Exception as e:
        log_error(f"Connection error: {str(e)}")
        return None
```

---

### 2. Register Product

**Endpoint**: `POST /api/external/efris/register-product`

**Request**:
```json
{
  "item_code": "PROD-001",
  "name": "Office Chair",
  "barcode": "1234567890123",
  "unit_price": 300000,
  "unit_of_measure": "PCS",
  "category_code": "1010101010104",
  "tax_rate": 18,
  "description": "Ergonomic office chair with lumbar support"
}
```

**Response**:
```json
{
  "success": true,
  "product_id": "uuid-here",
  "efris_product_code": "1000000000-PROD001",
  "registered_at": "2026-02-06T14:30:00Z"
}
```

---

### 3. Query Invoice Status

**Endpoint**: `GET /api/external/efris/query-invoice/{invoice_number}`

**Response**:
```json
{
  "invoice_number": "INV-2026-001",
  "status": "approved",
  "fdn": "1000000000-ABC-12345678",
  "submitted_at": "2026-02-06T14:30:00Z",
  "approved_at": "2026-02-06T14:30:15Z"
}
```

---

### 4. List Invoices

**Endpoint**: `GET /api/external/efris/invoices`

**Query Parameters**:
- `page` (default: 1)
- `limit` (default: 20, max: 100)
- `start_date` (format: YYYY-MM-DD)
- `end_date` (format: YYYY-MM-DD)
- `status` (pending|approved|rejected)

**Request**:
```http
GET /api/external/efris/invoices?page=1&limit=20&start_date=2026-02-01
```

**Response**:
```json
{
  "total": 150,
  "page": 1,
  "limit": 20,
  "invoices": [
    {
      "invoice_number": "INV-2026-001",
      "status": "approved",
      "fdn": "1000000000-ABC-12345678",
      "customer_name": "ABC Company",
      "total_amount": 5000000,
      "submitted_at": "2026-02-06T14:30:00Z"
    }
  ]
}
```

---

## 🔄 Integration Patterns

### Pattern 1: Real-Time Integration

**Use Case**: Submit to EFRIS immediately when invoice is created in ERP.

```python
# In your ERP's invoice creation flow

def create_invoice_in_erp(invoice_data):
    # 1. Save invoice to ERP database
    invoice_id = erp_db.save_invoice(invoice_data)
    
    # 2. Submit to EFRIS immediately
    efris_result = submit_invoice_to_efris(invoice_data)
    
    if efris_result and efris_result['success']:
        # 3. Update ERP with FDN
        erp_db.update_invoice(
            invoice_id,
            fdn=efris_result['fdn'],
            qr_code=efris_result['qr_code'],
            efris_status='approved'
        )
        
        # 4. Print invoice with FDN
        print_invoice(invoice_id)
    else:
        # 5. Mark for retry
        erp_db.update_invoice(
            invoice_id,
            efris_status='pending',
            error=efris_result.get('error')
        )
        
        # Queue for retry
        retry_queue.add(invoice_id)
    
    return invoice_id
```

**Pros**: Immediate FDN, customer gets receipt right away  
**Cons**: Blocks invoice creation if EFRIS is slow

---

### Pattern 2: Batch Processing

**Use Case**: Submit invoices in batches (hourly, daily).

```python
# Cron job: Run every hour

def process_pending_invoices():
    # 1. Get pending invoices
    pending = erp_db.get_invoices(status='pending_efris')
    
    print(f"Processing {len(pending)} invoices...")
    
    success_count = 0
    failure_count = 0
    
    for invoice in pending:
        # 2. Prepare EFRIS format
        efris_data = convert_erp_to_efris_format(invoice)
        
        # 3. Submit
        result = submit_invoice_to_efris(efris_data)
        
        if result and result['success']:
            # 4. Update status
            erp_db.update_invoice(
                invoice.id,
                fdn=result['fdn'],
                efris_status='approved'
            )
            success_count += 1
        else:
            # 5. Log error and retry later
            erp_db.log_error(invoice.id, result.get('error'))
            failure_count += 1
        
        # 6. Rate limiting (100 req/min)
        time.sleep(0.6)
    
    print(f"✅ Success: {success_count}, ❌ Failed: {failure_count}")
    
    # 7. Alert if high failure rate
    if failure_count > success_count:
        send_alert("High EFRIS failure rate!")
```

**Pros**: Doesn't block invoice creation, better error handling  
**Cons**: Delayed FDN, need retry logic

---

### Pattern 3: Webhook Integration

**Use Case**: EFRIS notifies your ERP when status changes.

```python
# Your ERP webhook endpoint

@app.route('/webhooks/efris', methods=['POST'])
def efris_webhook():
    # 1. Verify signature (security)
    signature = request.headers.get('X-EFRIS-Signature')
    if not verify_webhook_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    # 2. Parse webhook data
    webhook_data = request.json
    
    event_type = webhook_data['event']  # invoice.approved, invoice.rejected
    invoice_number = webhook_data['invoice_number']
    
    if event_type == 'invoice.approved':
        fdn = webhook_data['fdn']
        qr_code = webhook_data['qr_code']
        
        # 3. Update your ERP
        erp_db.update_invoice_by_number(
            invoice_number,
            fdn=fdn,
            qr_code=qr_code,
            efris_status='approved'
        )
        
        # 4. Notify customer via email/SMS
        send_invoice_notification(invoice_number)
        
    elif event_type == 'invoice.rejected':
        error = webhook_data['error']
        
        # 5. Mark as rejected
        erp_db.update_invoice_by_number(
            invoice_number,
            efris_status='rejected',
            error=error
        )
        
        # 6. Alert administrator
        send_admin_alert(f"Invoice {invoice_number} rejected: {error}")
    
    return jsonify({"status": "received"}), 200
```

**Setup webhook**:
```http
POST /api/external/efris/webhooks/subscribe
{
  "url": "https://your-erp.com/webhooks/efris",
  "events": ["invoice.approved", "invoice.rejected"],
  "secret": "your_webhook_secret"
}
```

---

## 💻 Code Examples

### Python (Django/Flask)

```python
# efris_integration.py

import os
import requests
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EFRISIntegration:
    def __init__(self):
        self.api_key = os.getenv('EFRIS_API_KEY')
        self.base_url = os.getenv(
            'EFRIS_BASE_URL',
            'https://efrisintegration.nafacademy.com/api/external/efris'
        )
        self.timeout = 30
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to EFRIS API"""
        
        url = f"{self.base_url}/{endpoint}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            if method == 'GET':
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.Timeout:
            logger.error(f"EFRIS timeout: {endpoint}")
            return {"success": False, "error": "Request timeout"}
        except requests.RequestException as e:
            logger.error(f"EFRIS request failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def submit_invoice(self, invoice_data: Dict) -> Dict:
        """Submit invoice to EFRIS"""
        return self._make_request('POST', 'submit-invoice', invoice_data)
    
    def register_product(self, product_data: Dict) -> Dict:
        """Register product with EFRIS"""
        return self._make_request('POST', 'register-product', product_data)
    
    def query_invoice(self, invoice_number: str) -> Dict:
        """Query invoice status"""
        return self._make_request('GET', f'query-invoice/{invoice_number}')
    
    def list_invoices(
        self,
        page: int = 1,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """List invoices with pagination"""
        
        params = {'page': page, 'limit': limit}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return self._make_request('GET', f'invoices?{query_string}')

# Usage
efris = EFRISIntegration()

# Submit invoice
result = efris.submit_invoice({
    "invoice_number": "INV-001",
    "customer_name": "ABC Ltd",
    "items": [...]
})

if result['success']:
    print(f"FDN: {result['fdn']}")
else:
    print(f"Error: {result['error']}")
```

---

### PHP (Laravel)

```php
<?php
// app/Services/EFRISService.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class EFRISService
{
    protected $apiKey;
    protected $baseUrl;
    protected $timeout;
    
    public function __construct()
    {
        $this->apiKey = env('EFRIS_API_KEY');
        $this->baseUrl = env(
            'EFRIS_BASE_URL',
            'https://efrisintegration.nafacademy.com/api/external/efris'
        );
        $this->timeout = 30;
    }
    
    protected function makeRequest($method, $endpoint, $data = null)
    {
        try {
            $response = Http::timeout($this->timeout)
                ->withHeaders([
                    'X-API-Key' => $this->apiKey,
                    'Content-Type' => 'application/json'
                ])
                ->$method("{$this->baseUrl}/{$endpoint}", $data);
            
            return $response->json();
            
        } catch (\Exception $e) {
            Log::error("EFRIS API error: " . $e->getMessage());
            return [
                'success' => false,
                'error' => $e->getMessage()
            ];
        }
    }
    
    public function submitInvoice(array $invoiceData)
    {
        return $this->makeRequest('post', 'submit-invoice', $invoiceData);
    }
    
    public function registerProduct(array $productData)
    {
        return $this->makeRequest('post', 'register-product', $productData);
    }
    
    public function queryInvoice(string $invoiceNumber)
    {
        return $this->makeRequest('get', "query-invoice/{$invoiceNumber}");
    }
}

// Usage in controller
use App\Services\EFRISService;

class InvoiceController extends Controller
{
    protected $efris;
    
    public function __construct(EFRISService $efris)
    {
        $this->efris = $efris;
    }
    
    public function submit(Request $request)
    {
        $invoiceData = [
            'invoice_number' => $request->invoice_number,
            'customer_name' => $request->customer_name,
            'items' => $request->items
        ];
        
        $result = $this->efris->submitInvoice($invoiceData);
        
        if ($result['success']) {
            // Update database with FDN
            Invoice::where('number', $request->invoice_number)
                ->update([
                    'fdn' => $result['fdn'],
                    'qr_code' => $result['qr_code'],
                    'efris_status' => 'approved'
                ]);
            
            return response()->json($result);
        } else {
            return response()->json($result, 400);
        }
    }
}
```

---

### JavaScript/Node.js

```javascript
// services/efrisService.js

const axios = require('axios');
const logger = require('./logger');

class EFRISService {
    constructor() {
        this.apiKey = process.env.EFRIS_API_KEY;
        this.baseUrl = process.env.EFRIS_BASE_URL ||
            'https://efrisintegration.nafacademy.com/api/external/efris';
        this.timeout = 30000;
    }
    
    async makeRequest(method, endpoint, data = null) {
        try {
            const config = {
                method,
                url: `${this.baseUrl}/${endpoint}`,
                headers: {
                    'X-API-Key': this.apiKey,
                    'Content-Type': 'application/json'
                },
                timeout: this.timeout
            };
            
            if (data) {
                config.data = data;
            }
            
            const response = await axios(config);
            return response.data;
            
        } catch (error) {
            logger.error('EFRIS API error:', error.message);
            
            if (error.response) {
                return error.response.data;
            }
            
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    async submitInvoice(invoiceData) {
        return await this.makeRequest('POST', 'submit-invoice', invoiceData);
    }
    
    async registerProduct(productData) {
        return await this.makeRequest('POST', 'register-product', productData);
    }
    
    async queryInvoice(invoiceNumber) {
        return await this.makeRequest('GET', `query-invoice/${invoiceNumber}`);
    }
    
    async listInvoices({ page = 1, limit = 20, startDate, endDate } = {}) {
        let query = `page=${page}&limit=${limit}`;
        if (startDate) query += `&start_date=${startDate}`;
        if (endDate) query += `&end_date=${endDate}`;
        
        return await this.makeRequest('GET', `invoices?${query}`);
    }
}

module.exports = new EFRISService();

// Usage in Express route
const efrisService = require('./services/efrisService');

app.post('/api/invoices/submit', async (req, res) => {
    const { invoice_number, customer_name, items } = req.body;
    
    const result = await efrisService.submitInvoice({
        invoice_number,
        customer_name,
        items
    });
    
    if (result.success) {
        // Update database
        await Invoice.update(
            { number: invoice_number },
            {
                fdn: result.fdn,
                qr_code: result.qr_code,
                efris_status: 'approved'
            }
        );
        
        res.json(result);
    } else {
        res.status(400).json(result);
    }
});
```

---

### C# (.NET)

```csharp
// EFRISService.cs

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

public class EFRISService
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<EFRISService> _logger;
    private readonly string _apiKey;
    private readonly string _baseUrl;
    
    public EFRISService(
        IHttpClientFactory httpClientFactory,
        IConfiguration configuration,
        ILogger<EFRISService> logger)
    {
        _httpClient = httpClientFactory.CreateClient();
        _logger = logger;
        _apiKey = configuration["EFRIS:ApiKey"];
        _baseUrl = configuration["EFRIS:BaseUrl"];
        
        _httpClient.DefaultRequestHeaders.Add("X-API-Key", _apiKey);
        _httpClient.Timeout = TimeSpan.FromSeconds(30);
    }
    
    public async Task<EFRISResponse> SubmitInvoiceAsync(InvoiceData invoice)
    {
        try
        {
            var json = JsonConvert.SerializeObject(invoice);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync(
                $"{_baseUrl}/submit-invoice",
                content
            );
            
            var responseContent = await response.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<EFRISResponse>(responseContent);
        }
        catch (Exception ex)
        {
            _logger.LogError($"EFRIS API error: {ex.Message}");
            return new EFRISResponse
            {
                Success = false,
                Error = ex.Message
            };
        }
    }
    
    public async Task<EFRISResponse> RegisterProductAsync(ProductData product)
    {
        var json = JsonConvert.SerializeObject(product);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await _httpClient.PostAsync(
            $"{_baseUrl}/register-product",
            content
        );
        
        var responseContent = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<EFRISResponse>(responseContent);
    }
}

// Models
public class InvoiceData
{
    [JsonProperty("invoice_number")]
    public string InvoiceNumber { get; set; }
    
    [JsonProperty("customer_name")]
    public string CustomerName { get; set; }
    
    [JsonProperty("items")]
    public List<InvoiceItem> Items { get; set; }
}

public class EFRISResponse
{
    [JsonProperty("success")]
    public bool Success { get; set; }
    
    [JsonProperty("fdn")]
    public string Fdn { get; set; }
    
    [JsonProperty("qr_code")]
    public string QrCode { get; set; }
    
    [JsonProperty("error")]
    public string Error { get; set; }
}

// Usage in controller
[ApiController]
[Route("api/[controller]")]
public class InvoiceController : ControllerBase
{
    private readonly EFRISService _efrisService;
    
    public InvoiceController(EFRISService efrisService)
    {
        _efrisService = efrisService;
    }
    
    [HttpPost("submit")]
    public async Task<IActionResult> Submit([FromBody] InvoiceData invoice)
    {
        var result = await _efrisService.SubmitInvoiceAsync(invoice);
        
        if (result.Success)
        {
            // Update database with FDN
            await _dbContext.Invoices
                .Where(i => i.Number == invoice.InvoiceNumber)
                .UpdateAsync(i => new Invoice
                {
                    Fdn = result.Fdn,
                    QrCode = result.QrCode,
                    EfrisStatus = "approved"
                });
            
            return Ok(result);
        }
        
        return BadRequest(result);
    }
}
```

---

## ⚠️ Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "specific_field",
    "value": "invalid_value"
  },
  "timestamp": "2026-02-06T14:30:00Z"
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `INVALID_API_KEY` | API key invalid or expired | Check key, regenerate if needed |
| `VALIDATION_ERROR` | Missing/invalid fields | Check request format |
| `RATE_LIMIT` | Too many requests | Wait and retry |
| `NETWORK_ERROR` | EFRIS connection failed | Retry with exponential backoff |
| `DUPLICATE_INVOICE` | Invoice number exists | Use unique invoice numbers |
| `EFRIS_ERROR` | EFRIS rejected invoice | Check EFRIS error details |

### Retry Logic

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, backoff=2):
    """Decorator for retrying failed requests"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                result = func(*args, **kwargs)
                
                if result.get('success'):
                    return result
                
                # Check if should retry
                error_code = result.get('error_code')
                should_retry = error_code in [
                    'NETWORK_ERROR',
                    'TIMEOUT',
                    'RATE_LIMIT'
                ]
                
                if should_retry and attempt < max_retries - 1:
                    wait_time = backoff ** attempt
                    logger.warning(
                        f"Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    return result
            
            return result
        return wrapper
    return decorator

# Usage
@retry_on_failure(max_retries=3, backoff=2)
def submit_invoice_with_retry(invoice_data):
    return efris.submit_invoice(invoice_data)
```

---

## 🧪 Testing

### Test Environment

```
Base URL: https://staging.efrisintegration.nafacademy.com/api/external/efris
Test API Key: efris_test_abc123...
```

### Unit Tests

```python
# test_efris_integration.py

import unittest
from unittest.mock import patch, Mock
from efris_integration import EFRISIntegration

class TestEFRISIntegration(unittest.TestCase):
    
    def setUp(self):
        self.efris = EFRISIntegration()
        self.test_invoice = {
            "invoice_number": "TEST-001",
            "customer_name": "Test Customer",
            "items": [
                {
                    "description": "Test Product",
                    "quantity": 1,
                    "unit_price": 10000,
                    "tax_rate": 18
                }
            ]
        }
    
    @patch('requests.post')
    def test_submit_invoice_success(self, mock_post):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "fdn": "1000000000-ABC-12345678"
        }
        mock_post.return_value = mock_response
        
        # Test
        result = self.efris.submit_invoice(self.test_invoice)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIn('fdn', result)
    
    @patch('requests.post')
    def test_submit_invoice_validation_error(self, mock_post):
        # Mock validation error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "error": "Missing required field: customer_tin"
        }
        mock_post.return_value = mock_response
        
        # Test
        result = self.efris.submit_invoice(self.test_invoice)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('error', result)

if __name__ == '__main__':
    unittest.main()
```

---

## ✅ Production Checklist

Before going live:

- [ ] **Security**
  - [ ] API keys stored in environment variables
  - [ ] HTTPS enabled
  - [ ] Webhook signatures verified
  - [ ] Rate limiting implemented

- [ ] **Reliability**
  - [ ] Retry logic implemented
  - [ ] Error logging configured
  - [ ] Monitoring/alerts set up
  - [ ] Timeout handling

- [ ] **Data**
  - [ ] FDN stored in database
  - [ ] QR codes saved
  - [ ] Invoice status tracked
  - [ ] Error logs maintained

- [ ] **Testing**
  - [ ] Unit tests pass
  - [ ] Integration tests complete
  - [ ] Load testing done
  - [ ] Edge cases covered

- [ ] **Documentation**
  - [ ] Integration guide for team
  - [ ] Error handling documented
  - [ ] Runbook created
  - [ ] Support contacts listed

---

## 📞 Support

- **Email**: support@efrisintegration.com
- **WhatsApp**: +256 XXX XXX XXX
- **Documentation**: https://docs.efrisintegration.com
- **Status Page**: https://status.efrisintegration.com

---

**Need help?** Open issue on GitHub or contact support team!
