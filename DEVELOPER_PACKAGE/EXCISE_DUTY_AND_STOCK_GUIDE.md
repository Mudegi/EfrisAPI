# Excise Duty Codes & Stock Management - Developer Guide

## 🎯 Overview

This guide shows ERP developers how to:
1. **Fetch excise duty codes** from EFRIS for product management
2. **Implement stock decrease** operations in your ERP

Both features are fully implemented in the backend and ready for integration into your ERP UI.

---

## Part 1: Excise Duty Codes

### What Are Excise Duty Codes?

Excise duty codes are EFRIS-specific classifications for products that have special tax treatment. Some products (alcohol, tobacco, fuel, electricity) have excise tax applied in addition to VAT.

Examples:
- LED190100 - Beer/Malt beverages
- LED200000 - Spirits (alcohol)
- LED190600 - Non-alcoholic drinks
- Various fuel and tobacco categories

### Use Cases in Your ERP

Your users will need excise codes when:
- ✅ Creating/updating product catalog
- ✅ Setting up product tax rates
- ✅ Configuring products for EFRIS submission
- ✅ Searching for excise-taxable goods

### API Endpoint: Fetch Excise Duty Codes

**Endpoint:**
```
GET /api/external/efris/excise-duty?token=test_token
GET /api/external/efris/excise-duty?token=test_token&excise_code=LED190100
GET /api/external/efris/excise-duty?token=test_token&excise_name=beer
```

**Authentication:** API Key in header
```http
X-API-Key: your_api_key
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | Use: "test_token" (for now) |
| `excise_code` | string | No | Filter by specific code (e.g., "LED190100") |
| `excise_name` | string | No | Filter by name (e.g., "beer") - partial match |

**Success Response (200 OK):**
```json
{
    "success": true,
    "status": "200",
    "message": "SUCCESS",
    "data": {
        "exciseDutyList": [
            {
                "exciseDutyCode": "LED190100",
                "goodService": "Beer and malt beverages",
                "effectiveDate": "01/07/2021",
                "parentCode": "LED190000",
                "rateText": "10%",
                "isLeafNode": "1",
                "exciseDutyDetailsList": [
                    {
                        "exciseDutyId": "120453215404593459",
                        "rate": "0.10",
                        "type": "101"
                    }
                ]
            },
            {
                "exciseDutyCode": "LED200100",
                "goodService": "Spirits and alcohol",
                "effectiveDate": "01/07/2021",
                "parentCode": "LED200000",
                "rateText": "15%",
                "isLeafNode": "1",
                "exciseDutyDetailsList": [
                    {
                        "exciseDutyId": "120453215404593460",
                        "rate": "0.15",
                        "type": "101"
                    }
                ]
            }
        ]
    }
}
```

**Error Response (400 Bad Request):**
```json
{
    "success": false,
    "error_code": "400",
    "message": "Invalid request parameters"
}
```

### Frontend Implementation Example

#### JavaScript/TypeScript

```typescript
// Function to fetch excise duty codes
async function fetchExciseDutyCodes(filterCode?: string, filterName?: string) {
    const params = new URLSearchParams({ token: 'test_token' });
    
    if (filterCode) params.append('excise_code', filterCode);
    if (filterName) params.append('excise_name', filterName);
    
    const response = await fetch(
        `/api/external/efris/excise-duty?${params.toString()}`,
        {
            headers: {
                'X-API-Key': process.env.REACT_APP_EFRIS_API_KEY,
                'Content-Type': 'application/json'
            }
        }
    );
    
    const data = await response.json();
    
    if (!data.success) {
        throw new Error(data.message || 'Failed to fetch excise codes');
    }
    
    return data.data.exciseDutyList;
}

// Usage in product form
async function handleProductFormLoad() {
    try {
        const exciseCodes = await fetchExciseDutyCodes();
        
        // Populate dropdown/autocomplete
        const selectElement = document.getElementById('excise-code-select');
        exciseCodes.forEach(code => {
            const option = document.createElement('option');
            option.value = code.exciseDutyCode;
            option.textContent = `${code.exciseDutyCode} - ${code.goodService} (${code.rateText})`;
            selectElement.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading excise codes:', error);
    }
}

// Search/filter excise codes
async function searchExciseCodes(searchTerm: string) {
    try {
        const codes = await fetchExciseDutyCodes(undefined, searchTerm);
        return codes;
    } catch (error) {
        console.error('Error searching excise codes:', error);
        return [];
    }
}
```

#### React Component Example

```jsx
import React, { useState, useEffect } from 'react';

function ExciseDutySelector() {
    const [exciseCodes, setExciseCodes] = useState([]);
    const [loading, setLoading] = useState(false);
    const [search, setSearch] = useState('');

    useEffect(() => {
        loadExciseCodes();
    }, []);

    async function loadExciseCodes() {
        setLoading(true);
        try {
            const response = await fetch(
                `/api/external/efris/excise-duty?token=test_token${
                    search ? `&excise_name=${encodeURIComponent(search)}` : ''
                }`,
                {
                    headers: {
                        'X-API-Key': process.env.REACT_APP_EFRIS_API_KEY
                    }
                }
            );
            const data = await response.json();
            setExciseCodes(data.data?.exciseDutyList || []);
        } catch (error) {
            console.error('Error loading excise codes:', error);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="excise-duty-selector">
            <label>Excise Duty Code</label>
            <input
                type="text"
                placeholder="Search excise codes..."
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    // Debounce in production
                    setTimeout(loadExciseCodes, 300);
                }}
            />
            
            {loading && <p>Loading...</p>}
            
            <select name="excise_code">
                <option value="">-- Select Excise Code --</option>
                {exciseCodes.map(code => (
                    <option key={code.exciseDutyCode} value={code.exciseDutyCode}>
                        {code.exciseDutyCode} - {code.goodService} ({code.rateText})
                    </option>
                ))}
            </select>
        </div>
    );
}

export default ExciseDutySelector;
```

#### HTML/jQuery Example

```html
<form id="product-form">
    <label for="excise-code">Excise Duty Code:</label>
    <input type="text" id="excise-search" placeholder="Search...">
    <select id="excise-code-select" name="excise_code">
        <option value="">-- Loading --</option>
    </select>
</form>

<script>
$(document).ready(function() {
    // Load excise codes on page load
    function loadExciseCodes(search = '') {
        const url = `/api/external/efris/excise-duty?token=test_token${
            search ? `&excise_name=${search}` : ''
        }`;
        
        $.ajax({
            url: url,
            headers: {
                'X-API-Key': $('[data-api-key]').data('api-key')
            },
            success: function(data) {
                const select = $('#excise-code-select');
                select.empty().append('<option value="">-- Select Code --</option>');
                
                data.data.exciseDutyList.forEach(code => {
                    select.append(
                        `<option value="${code.exciseDutyCode}">
                            ${code.exciseDutyCode} - ${code.goodService} (${code.rateText})
                        </option>`
                    );
                });
            },
            error: function(error) {
                console.error('Error loading excise codes:', error);
            }
        });
    }
    
    // Load on page load
    loadExciseCodes();
    
    // Search/filter
    let searchTimeout;
    $('#excise-search').on('keyup', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadExciseCodes($(this).val());
        }, 300);
    });
});
</script>
```

#### Python/Flask Example

```python
import requests
from flask import request, jsonify

@app.route('/api/products/excise-codes', methods=['GET'])
def get_excise_codes():
    """Fetch excise codes from EFRIS"""
    search = request.args.get('search', '')
    
    # Call backend EFRIS API
    url = "https://efrisintegration.nafacademy.com/api/external/efris/excise-duty"
    params = {'token': 'test_token'}
    
    if search:
        params['excise_name'] = search
    
    headers = {
        'X-API-Key': os.getenv('EFRIS_API_KEY')
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if data['success']:
            codes = data['data']['exciseDutyList']
            return jsonify({
                'success': True,
                'codes': [
                    {
                        'code': c['exciseDutyCode'],
                        'name': c['goodService'],
                        'rate': c['rateText']
                    }
                    for c in codes
                ]
            })
        else:
            return jsonify({'success': False, 'error': data['message']}), 400
            
    except requests.RequestException as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### Integration Checklist

- [ ] Add API endpoint to your ERP
- [ ] Create product selection UI component
- [ ] Add search/filter functionality
- [ ] Display excise code with rate in product list
- [ ] Store selected excise code in product database
- [ ] Include excise code when submitting to EFRIS

---

## Part 2: Stock Decrease Operations

### What Is Stock Decrease?

Stock decrease (T132) allows you to:
- ✅ Remove damaged goods from inventory
- ✅ Record expired items disposal
- ✅ Account for employee usage
- ✅ Handle inventory discrepancies
- ✅ Track raw material consumption

This creates an audit trail with EFRIS for regulatory compliance.

### Why Track Stock Decreases?

1. **Regulatory Compliance** - EFRIS requires tracking
2. **Inventory Accuracy** - Maintain proper stock records
3. **Tax Deduction** - Document losses for tax purposes
4. **Audit Trail** - Complete history of all adjustments

### API Endpoint: Stock Decrease

**Endpoint:**
```
POST /api/external/efris/stock-decrease
```

**Authentication:**
```http
X-API-Key: your_api_key
Content-Type: application/json
```

**Request Body:**

```json
{
    "operationType": "102",
    "adjustType": "102",
    "stockInDate": "2024-02-04",
    "remarks": "Water damaged in warehouse",
    "goodsStockInItem": [
        {
            "goodsCode": "SKU-001",
            "measureUnit": "101",
            "quantity": 5,
            "unitPrice": 5000,
            "remarks": "Damaged units"
        },
        {
            "goodsCode": "SKU-002",
            "measureUnit": "102",
            "quantity": 10,
            "unitPrice": 10000,
            "remarks": "Expired items"
        }
    ]
}
```

**Request Parameters:**

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| `operationType` | string | Yes | "102" | Always 102 for decrease |
| `adjustType` | string | Yes | 101-105 | Reason for removal |
| `stockInDate` | string | No | YYYY-MM-DD | When adjustment occurred |
| `remarks` | string | No* | Any text | *Required if adjustType = 104 |

**Adjustment Types (adjustType values):**

| Code | Type | Use When | Example |
|------|------|----------|---------|
| **101** | Expired | Items past expiration | Medicine, dairy products |
| **102** | Damaged | Physical damage/defects | Broken packaging, dents |
| **103** | Personal Use | Employee consumed item | Staff meals, samples |
| **104** | Others | Custom reason | **Remarks field REQUIRED** |
| **105** | Raw Materials | Raw materials consumed | Ingredients used in production |

**Item Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `goodsCode` | string | Yes | Product/SKU code |
| `measureUnit` | string | No | Unit code (101=kg, 102=pieces, etc.) |
| `quantity` | number | Yes | Units to remove |
| `unitPrice` | number | Yes | Unit cost (for valuation) |
| `remarks` | string | No | Item-specific notes |

**Success Response (200 OK):**

```json
{
    "returnStateInfo": {
        "returnCode": "00",
        "returnMessage": "SUCCESS"
    },
    "data": {
        "decrypted_content": [
            {
                "goodsCode": "SKU-001",
                "quantity": "5",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            },
            {
                "goodsCode": "SKU-002",
                "quantity": "10",
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            }
        ]
    }
}
```

**Error Response (400 Bad Request):**

```json
{
    "returnStateInfo": {
        "returnCode": "2127",
        "returnMessage": "adjustType cannot be empty!"
    }
}
```

### Common Error Codes

| Code | Message | How to Fix |
|------|---------|-----------|
| 2076 | operationType cannot be empty | Use "102" |
| 2127 | adjustType cannot be empty | Provide adjustment reason (101-105) |
| 2194 | goodsCode cannot be empty | Include product code |
| 2282 | Insufficient stock | Check available quantity before submit |
| 2890 | remarks cannot be empty (adjustType 104) | Provide remarks when using type 104 |

### Frontend Implementation Example

#### JavaScript/TypeScript

```typescript
// Function to submit stock decrease
async function submitStockDecrease(
    items: StockItem[],
    adjustType: string,
    remarks: string
) {
    const payload = {
        operationType: "102",
        adjustType: adjustType,
        stockInDate: new Date().toISOString().split('T')[0],
        remarks: remarks,
        goodsStockInItem: items
    };

    const response = await fetch('/api/external/efris/stock-decrease', {
        method: 'POST',
        headers: {
            'X-API-Key': process.env.REACT_APP_EFRIS_API_KEY,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
        const errorMsg = data.returnStateInfo?.returnMessage || 
                        'Failed to process stock decrease';
        throw new Error(errorMsg);
    }

    return data;
}

// Type definition
interface StockItem {
    goodsCode: string;
    measureUnit: string;
    quantity: number;
    unitPrice: number;
    remarks?: string;
}

// Usage in form
async function handleStockDecreaseSubmit(formData: FormData) {
    try {
        // Parse form items
        const items: StockItem[] = [
            {
                goodsCode: formData.get('item_code') as string,
                measureUnit: '101',
                quantity: parseInt(formData.get('quantity') as string),
                unitPrice: parseFloat(formData.get('unit_price') as string),
                remarks: formData.get('item_remarks') as string
            }
        ];

        const result = await submitStockDecrease(
            items,
            formData.get('adjust_type') as string,
            formData.get('remarks') as string
        );

        // Show success message
        if (result.returnStateInfo.returnCode === '00') {
            alert('✓ Stock decrease recorded successfully');
            // Refresh inventory list
            location.reload();
        }
    } catch (error) {
        alert(`✗ Error: ${error.message}`);
    }
}
```

#### React Component Example

```jsx
import React, { useState } from 'react';

function StockDecreaseForm() {
    const [items, setItems] = useState([
        { goodsCode: '', measureUnit: '101', quantity: 0, unitPrice: 0, remarks: '' }
    ]);
    const [adjustType, setAdjustType] = useState('102');
    const [remarks, setRemarks] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const addItem = () => {
        setItems([
            ...items,
            { goodsCode: '', measureUnit: '101', quantity: 0, unitPrice: 0, remarks: '' }
        ]);
    };

    const updateItem = (index, field, value) => {
        const newItems = [...items];
        newItems[index][field] = value;
        setItems(newItems);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage('');

        try {
            const payload = {
                operationType: '102',
                adjustType: adjustType,
                stockInDate: new Date().toISOString().split('T')[0],
                remarks: remarks,
                goodsStockInItem: items.filter(item => item.goodsCode)
            };

            const response = await fetch('/api/external/efris/stock-decrease', {
                method: 'POST',
                headers: {
                    'X-API-Key': process.env.REACT_APP_EFRIS_API_KEY,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.returnStateInfo.returnCode === '00') {
                setMessage('✓ Stock decrease recorded successfully!');
                setItems([{ goodsCode: '', measureUnit: '101', quantity: 0, unitPrice: 0, remarks: '' }]);
                setAdjustType('102');
                setRemarks('');
            } else {
                setMessage(`✗ Error: ${data.returnStateInfo.returnMessage}`);
            }
        } catch (error) {
            setMessage(`✗ Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="stock-decrease-form">
            <h2>Record Stock Decrease</h2>

            {message && <div className="message">{message}</div>}

            <div className="form-group">
                <label>Adjustment Type:</label>
                <select value={adjustType} onChange={(e) => setAdjustType(e.target.value)}>
                    <option value="101">101 - Expired Goods</option>
                    <option value="102">102 - Damaged Goods</option>
                    <option value="103">103 - Personal Use</option>
                    <option value="104">104 - Others (requires remarks)</option>
                    <option value="105">105 - Raw Materials</option>
                </select>
            </div>

            <div className="form-group">
                <label>Remarks:</label>
                <textarea
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    placeholder={adjustType === '104' ? 'REQUIRED for type 104' : 'Optional'}
                    required={adjustType === '104'}
                />
            </div>

            <h3>Items to Remove</h3>
            {items.map((item, index) => (
                <div key={index} className="item-row">
                    <input
                        type="text"
                        placeholder="Product Code"
                        value={item.goodsCode}
                        onChange={(e) => updateItem(index, 'goodsCode', e.target.value)}
                        required
                    />
                    <input
                        type="number"
                        placeholder="Quantity"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value))}
                        required
                    />
                    <input
                        type="number"
                        placeholder="Unit Price"
                        value={item.unitPrice}
                        onChange={(e) => updateItem(index, 'unitPrice', parseFloat(e.target.value))}
                        required
                    />
                    <input
                        type="text"
                        placeholder="Item remarks"
                        value={item.remarks}
                        onChange={(e) => updateItem(index, 'remarks', e.target.value)}
                    />
                </div>
            ))}

            <button type="button" onClick={addItem}>+ Add Item</button>

            <button type="submit" disabled={loading}>
                {loading ? 'Processing...' : 'Submit Stock Decrease'}
            </button>
        </form>
    );
}

export default StockDecreaseForm;
```

#### HTML/jQuery Example

```html
<form id="stock-decrease-form">
    <h2>Record Stock Decrease</h2>

    <div class="form-group">
        <label>Adjustment Type:</label>
        <select id="adjust-type" name="adjust_type">
            <option value="101">101 - Expired Goods</option>
            <option value="102" selected>102 - Damaged Goods</option>
            <option value="103">103 - Personal Use</option>
            <option value="104">104 - Others</option>
            <option value="105">105 - Raw Materials</option>
        </select>
    </div>

    <div class="form-group">
        <label>Remarks:</label>
        <textarea id="remarks" name="remarks" rows="3"></textarea>
    </div>

    <h3>Items</h3>
    <table id="items-table">
        <thead>
            <tr>
                <th>Product Code</th>
                <th>Quantity</th>
                <th>Unit Price</th>
                <th>Remarks</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            <tr class="item-row">
                <td><input type="text" class="goods-code" placeholder="SKU-001"></td>
                <td><input type="number" class="quantity" placeholder="5"></td>
                <td><input type="number" class="unit-price" placeholder="5000"></td>
                <td><input type="text" class="item-remarks"></td>
                <td><button type="button" class="remove-item">Remove</button></td>
            </tr>
        </tbody>
    </table>

    <button type="button" id="add-item">+ Add Item</button>
    <button type="submit">Submit Stock Decrease</button>
</form>

<script>
$(document).ready(function() {
    // Add new item row
    $('#add-item').click(function() {
        $('#items-table tbody').append(`
            <tr class="item-row">
                <td><input type="text" class="goods-code" placeholder="SKU-001"></td>
                <td><input type="number" class="quantity" placeholder="5"></td>
                <td><input type="number" class="unit-price" placeholder="5000"></td>
                <td><input type="text" class="item-remarks"></td>
                <td><button type="button" class="remove-item">Remove</button></td>
            </tr>
        `);
    });

    // Remove item row
    $(document).on('click', '.remove-item', function() {
        $(this).closest('tr').remove();
    });

    // Submit form
    $('#stock-decrease-form').submit(function(e) {
        e.preventDefault();

        const items = [];
        $('.item-row').each(function() {
            items.push({
                goodsCode: $(this).find('.goods-code').val(),
                measureUnit: '101',
                quantity: parseInt($(this).find('.quantity').val()),
                unitPrice: parseFloat($(this).find('.unit-price').val()),
                remarks: $(this).find('.item-remarks').val()
            });
        });

        const payload = {
            operationType: '102',
            adjustType: $('#adjust-type').val(),
            stockInDate: new Date().toISOString().split('T')[0],
            remarks: $('#remarks').val(),
            goodsStockInItem: items
        };

        $.ajax({
            url: '/api/external/efris/stock-decrease',
            type: 'POST',
            headers: {
                'X-API-Key': $('[data-api-key]').data('api-key'),
                'Content-Type': 'application/json'
            },
            data: JSON.stringify(payload),
            success: function(data) {
                if (data.returnStateInfo.returnCode === '00') {
                    alert('✓ Stock decrease recorded successfully');
                    location.reload();
                } else {
                    alert('✗ Error: ' + data.returnStateInfo.returnMessage);
                }
            },
            error: function(error) {
                alert('✗ Error: ' + error.responseJSON?.returnStateInfo?.returnMessage || 'Unknown error');
            }
        });
    });
});
</script>
```

#### Python/Flask Example

```python
@app.route('/api/inventory/stock-decrease', methods=['POST'])
def record_stock_decrease():
    """Record stock decrease in your ERP"""
    data = request.json
    
    try:
        # Prepare payload for EFRIS backend
        payload = {
            'operationType': '102',
            'adjustType': data.get('adjustType'),
            'stockInDate': data.get('stockInDate', datetime.now().strftime('%Y-%m-%d')),
            'remarks': data.get('remarks', ''),
            'goodsStockInItem': data.get('items', [])
        }
        
        # Call EFRIS backend API
        response = requests.post(
            'https://efrisintegration.nafacademy.com/api/external/efris/stock-decrease',
            json=payload,
            headers={
                'X-API-Key': os.getenv('EFRIS_API_KEY'),
                'Content-Type': 'application/json'
            }
        )
        
        result = response.json()
        
        if result.get('returnStateInfo', {}).get('returnCode') == '00':
            # Save to local database
            adjustment = StockAdjustment(
                adjustment_type=data.get('adjustType'),
                remarks=data.get('remarks'),
                items=json.dumps(data.get('items')),
                efris_status='SUCCESS'
            )
            db.session.add(adjustment)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Stock decrease recorded'}), 200
        else:
            return jsonify({'success': False, 'message': result.get('returnStateInfo', {}).get('returnMessage')}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
```

### Integration Checklist

- [ ] Add stock decrease form to inventory module
- [ ] Create dropdown for adjustment types (101-105)
- [ ] Implement remarks field (required for type 104)
- [ ] Build item table with product code, quantity, price
- [ ] Add validation (check sufficient stock before submit)
- [ ] Integrate API call to backend
- [ ] Display success/error messages
- [ ] Store adjustment records locally
- [ ] Show adjustment history in inventory

---

## Testing Your Integration

### Test Excise Duty Fetch

```bash
curl -X GET "https://efrisintegration.nafacademy.com/api/external/efris/excise-duty?token=test_token" \
  -H "X-API-Key: your_api_key"
```

### Test Stock Decrease

```bash
curl -X POST "https://efrisintegration.nafacademy.com/api/external/efris/stock-decrease" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "operationType": "102",
    "adjustType": "102",
    "stockInDate": "2024-02-04",
    "remarks": "Damaged goods",
    "goodsStockInItem": [{
      "goodsCode": "SKU-001",
      "quantity": 5,
      "unitPrice": 5000
    }]
  }'
```

---

## Summary

### Excise Duty Feature

✅ Get EFRIS excise duty codes  
✅ Filter by code or name  
✅ Display in product forms  
✅ Store with products  
✅ Include in EFRIS submissions  

**Time to Implement:** 2-4 hours

### Stock Decrease Feature

✅ Remove goods from inventory  
✅ Track 5 adjustment types  
✅ Batch multiple items  
✅ Maintain audit trail  
✅ Full error handling  

**Time to Implement:** 4-6 hours

Both features are **production-ready** in the backend and just need UI integration in your ERP.
