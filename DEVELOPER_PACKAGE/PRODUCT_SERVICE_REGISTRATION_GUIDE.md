# Product/Service Registration Guide

Complete guide for registering products and services with EFRIS via the External API.

---

## Table of Contents
- [Overview](#overview)
- [API Endpoint](#api-endpoint)
- [Required Fields](#required-fields)
- [Field Specifications](#field-specifications)
- [Product Code Logic](#product-code-logic)
- [Excise Duty Integration](#excise-duty-integration)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [EFRIS Field Mappings](#efris-field-mappings)

---

## Overview

**Purpose**: Register products and services in EFRIS before they can be used in invoices.

**EFRIS Interface**: T130 - Goods Upload  
**Endpoint**: `POST /api/external/efris/register-product`  
**Authentication**: X-API-Key header

**Important Notes**:
- All products/services MUST be registered with EFRIS before they can appear on fiscalized invoices
- The API accepts simplified fields and maps them to EFRIS T130 format
- Commodity Category ID (`commodityCategoryId`) is EFRIS's item category classification, not UNSPC

---

## API Endpoint

### Base URL
```
https://efrisintegration.nafacademy.com/api/external/efris/register-product
```

### Method
```
POST
```

### Headers
```http
Content-Type: application/json
X-API-Key: your_api_key_here
```

---

## Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_code` | string | ✅ Yes | Unique product identifier  |
| `item_name` | string | ✅ Yes | Product/service name |
| `unit_price` | number | ✅ Yes | Unit price in UGX |
| `commodity_code` | string | ✅ Yes | UNSPC commodity category code |
| `unit_of_measure` | string | Optional | Unit of measure code (default: "102" = Pieces) |
| `have_excise_tax` | string | Optional | Whether product has excise duty (default: "102" = No) |
| `excise_duty_code` | string | Conditional | Required if `have_excise_tax` = "101" |
| `stock_quantity` | number | Optional | Low stock warning threshold (default: 0) |
| `description` | string | Optional | Product description/remarks |

---

## Field Specifications

### 1. Product Code (`item_code`)

**Your ERP Field**: SKU / Product Code / Item Code  
**EFRIS Field**: `goodsCode`  
**Format**: String, alphanumeric  

**Logic**:
```
IF product_code exists in ERP:
    use product_code
ELSE IF item_description exists:
    use item_description (sanitized)
ELSE:
    use product_name (sanitized)
```

**Example**:
```javascript
// In your ERP
const itemCode = product.sku || 
                 sanitize(product.description) || 
                 sanitize(product.name);
```

**Sanitization Rules**:
- Remove special characters (keep alphanumeric, hyphens, underscores)
- Trim whitespace
- Max length: 50 characters
- Cannot be empty

---

### 2. Product Name (`item_name`)

**Your ERP Field**: Product Name / Item Name / Service Name  
**EFRIS Field**: `goodsName`  
**Format**: String  

**Rules**:
- Cannot be empty
- Max length: 200 characters
- Use full descriptive name
- Include brand/variant if applicable

**Examples**:
- ✅ "Coca-Cola 500ml Bottle"
- ✅ "Cement 50kg Bag"
- ✅ "Accounting Consultation Service"
- ❌ "" (empty)
- ❌ "Prod" (too generic)

---

### 3. Unit Price (`unit_price`)

**Your ERP Field**: Selling Price / Unit Price  
**EFRIS Field**: `unitPrice`  
**Format**: Number (sent as string to EFRIS)  

**Rules**:
- Must be positive number
- Decimal values allowed
- Currency: Always UGX (Ugandan Shillings)
- Send without currency symbol

**Examples**:
```json
{
  "unit_price": 5000,      // ✅ UGX 5,000
  "unit_price": 12500.50,  // ✅ UGX 12,500.50
  "unit_price": 0          // ❌ Invalid (must be > 0)
}
```

---

### 4. Commodity Category Code (`commodity_code`)

**Your ERP Field**: Commodity Category / Item Category Code  
**EFRIS Field**: `commodityCategoryId`  
**Format**: String (up to 18 digits)  

**What is it?**: EFRIS Commodity Category ID - NOT the same as product code. This is the item category classification used by EFRIS to group similar products.

**How to get it**: 
1. Query commodity category codes from EFRIS using T134 interface (endpoint coming soon)
2. User selects category during product creation in your ERP
3. Store in your ERP's product master data

**Note**: This is the Item Category ID from EFRIS, not UNSPC. EFRIS provides its own commodity category classification system.

**Common Codes**:
| Code | Category | Example Products |
|------|----------|------------------|
| `10111301` | General Goods | Miscellaneous items |
| `50000000` | Food & Beverage | Drinks, packaged food |
| `44000000` | Office Supplies | Paper, pens, stationery |
| `30000000` | Hardware | Tools, equipment |

**Storage in ERP**:
```typescript
// Product schema in your ERP
interface Product {
  id: string;
  sku: string;
  name: string;
  commodityCode: string;     // ← Store this during product creation
  commodityName?: string;    // ← Optional, for display
  // ... other fields
}
```

---

### 5. Unit of Measure (`unit_of_measure`)

**Your ERP Field**: Unit / UOM  
**EFRIS Field**: `measureUnit`  
**Format**: String (3-digit code)  
**Default**: "102" (Pieces)

**EFRIS Unit Codes**:
| Code | Unit | Use For |
|------|------|---------|
| `101` | Piece | Individual items |
| `102` | Box/Carton | Packaged goods |
| `103` | Dozen | Sets of 12 |
| `104` | Kilogram | Weight-based products |
| `105` | Meter | Length-based products |
| `106` | Liter | Liquid volumes |
| `107` | Ton | Heavy goods |
| `108` | Square Meter | Area-based products |
| `109` | Cubic Meter | Volume-based products |
| `110` | Service | Professional services |

**Mapping** from your ERP:
```javascript
// ERP unit mappings
const UNIT_MAP = {
  'pcs': '101',
  'piece': '101',
  'each': '101',
  'box': '102',
  'carton': '102',
  'dozen': '103',
  'kg': '104',
  'kilogram': '104',
  'meter': '105',
  'litre': '106',
  'liter': '106',
  'service': '110',
  // ... add more as needed
};

const efrisUnit = UNIT_MAP[product.unit.toLowerCase()] || '102';
```

---

### 6. Excise Duty Configuration

#### A. Have Excise Tax (`have_excise_tax`)

**Your ERP Field**: Checkbox "Subject to Excise Duty"  
**EFRIS Field**: `haveExciseTax`  
**Format**: String  
**Default**: "102" (No)

**Values**:
- `"101"` = Yes (product is subject to excise duty)
- `"102"` = No (product is not subject to excise duty)

**Products Subject to Excise Duty**:
- Alcoholic beverages (beer, wine, spirits)
- Tobacco products (cigarettes, cigars)
- Soft drinks and juices
- Plastic products
- Fuel and petroleum products
- Cement
- Sugar
- Mobile data services

**Example in ERP**:
```typescript
interface Product {
  // ...
  hasExciseDuty: boolean;  // User checkbox
  exciseDutyCode?: string; // Populated if hasExciseDuty = true
}

// When sending to API
const payload = {
  have_excise_tax: product.hasExciseDuty ? "101" : "102",
  excise_duty_code: product.hasExciseDuty ? product.exciseDutyCode : undefined
};
```

#### B. Excise Duty Code (`excise_duty_code`)

**Your ERP Field**: Excise Duty Code selector  
**EFRIS Field**: `exciseDutyCode`  
**Format**: String (e.g., "LED190100")  
**Required When**: `have_excise_tax` = "101"

**How to get codes**:
```http
GET /api/external/efris/excise-duty
X-API-Key: your_api_key
```

**Response**:
```json
{
  "success": true,
  "excise_codes": [
    {
      "code": "LED190100",
      "name": "Fruit juice and vegetable juice",
      "rate": "250",
      "unit": "102",
      "currency": "UGX",
      "excise_rule": "2"
    }
  ]
}
```

**Storage**:
```typescript
// In product creation form
const [exciseDuty, setExciseDuty] = useState({
  hasExcise: false,
  code: '',
  name: ''
});

// When user selects excise code
setExciseDuty({
  hasExcise: true,
  code: 'LED190100',
  name: 'Fruit juice and vegetable juice'
});

// Save to product record
product.exciseDutyCode = exciseDuty.code;
```

---

### 7. Product Type (Product vs Service)

**EFRIS Field**: `goodsTypeCode`  
**Format**: String  
**Values**:  
- `"101"` = Goods (physical products)
- `"102"` = Fuel (gas stations)

**Default**: "101" (Goods)

**Note**: Services are also registered as `goodsTypeCode="101"` but with service-appropriate measure units (e.g., "110" for service hours)

**Examples**:
```json
// Product
{
  "item_name": "Coca-Cola 500ml",
  "unit_of_measure": "106",  // Liter
  "unit_price": 2500,
  "goods_type_code": "101"  // Goods (default)
}

// Service
{
  "item_name": "Accounting Consultation",
  "unit_of_measure": "110",  // Service hours
  "unit_price": 150000,
  "goods_type_code": "101"  // Still "Goods" even for services
}
```

---

## Product Code Logic

Detailed logic for determining product codes:

```javascript
/**
 * Determine product code for EFRIS registration
 * @param {Object} product - Product from your ERP
 * @returns {string} - Product code to use
 */
function getProductCode(product) {
  // Priority 1: Use explicit product code/SKU
  if (product.sku && product.sku.trim()) {
    return sanitizeCode(product.sku);
  }
  
  // Priority 2: Use item description
  if (product.itemDescription && product.itemDescription.trim()) {
    return sanitizeCode(product.itemDescription);
  }
  
  // Priority 3: Use product name
  if (product.name && product.name.trim()) {
    return sanitizeCode(product.name);
  }
  
  // Fallback: Generate from ID
  return `PROD-${product.id}`;
}

/**
 * Sanitize code for EFRIS compliance
 */
function sanitizeCode(code) {
  return code
    .trim()
    .replace(/[^a-zA-Z0-9-_]/g, '')  // Remove special chars
    .substring(0, 50)                 // Max 50 chars
    .toUpperCase();                   // Uppercase
}
```

**Examples**:

| ERP Data | Result |
|----------|--------|
| `sku: "PROD-001"` | `PROD-001` |
| `sku: "", description: "Cement 50kg"` | `CEMENT50KG` |
| `sku: "", description: "", name: "Super Glue"` | `SUPERGLUE` |
| `sku: "Beer-500ml!"` | `BEER-500ML` |

---

## Excise Duty Integration

### Step-by-Step Implementation

#### 1. Fetch Excise Codes

```typescript
async function fetchExciseCodes(apiKey: string) {
  const response = await fetch(
    'https://efrisintegration.nafacademy.com/api/external/efris/excise-duty',
    {
      headers: {
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      }
    }
  );
  
  const data = await response.json();
  return data.excise_codes; // Array of excise codes
}
```

#### 2. UI Component (Excise Selector)

```typescript
// ExciseDutySelector.tsx
interface ExciseDutySelectorProps {
  value?: string;
  onChange: (code: string, name: string) => void;
  apiKey: string;
}

function ExciseDutySelector({ value, onChange, apiKey }: ExciseDutySelectorProps) {
  const [codes, setCodes] = useState([]);
  const [search, setSearch] = useState('');
  
  useEffect(() => {
    fetchExciseCodes(apiKey).then(setCodes);
  }, [apiKey]);
  
  const filtered = codes.filter(c => 
    c.code.includes(search) || 
    c.name.toLowerCase().includes(search.toLowerCase())
  );
  
  return (
    <div>
      <input 
        type="text" 
        placeholder="Search by code or name..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <select 
        value={value} 
        onChange={e => {
          const selected = codes.find(c => c.code === e.target.value);
          if (selected) onChange(selected.code, selected.name);
        }}
      >
        <option value="">-- Select Excise Code --</option>
        {filtered.map(code => (
          <option key={code.code} value={code.code}>
            {code.code} - {code.name}
          </option>
        ))}
      </select>
    </div>
  );
}
```

#### 3. Product Form Integration

```typescript
// ProductForm.tsx
function ProductForm() {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    unitPrice: 0,
    commodityCode: '',
    unitOfMeasure: '102',
    hasExciseDuty: false,
    exciseDutyCode: '',
    exciseDutyName: ''
  });
  
  return (
    <form>
      {/* ... other fields ... */}
      
      {/* Excise Duty Checkbox */}
      <label>
        <input 
          type="checkbox"
          checked={formData.hasExciseDuty}
          onChange={e => setFormData({
            ...formData,
            hasExciseDuty: e.target.checked,
            exciseDutyCode: e.target.checked ? formData.exciseDutyCode : ''
          })}
        />
        Subject to Excise Duty
      </label>
      
      {/* Excise Code Selector - Only if checkbox is checked */}
      {formData.hasExciseDuty && (
        <ExciseDutySelector
          value={formData.exciseDutyCode}
          onChange={(code, name) => setFormData({
            ...formData,
            exciseDutyCode: code,
            exciseDutyName: name
          })}
          apiKey={YOUR_API_KEY}
        />
      )}
    </form>
  );
}
```

---

## Request/Response Examples

### Example 1: Simple Product (No Excise)

**Request**:
```http
POST /api/external/efris/register-product
X-API-Key: efris_opVNle8KcO92KlXshJ1sSRT30y61sn3SKl3ExUv83Vw
Content-Type: application/json

{
  "item_code": "CEMENT-50KG",
  "item_name": "Cement 50kg Bag",
  "unit_price": 32000,
  "commodity_code": "30201000",
  "unit_of_measure": "104",
  "have_excise_tax": "102",
  "stock_quantity": 100,
  "description": "Portland cement, 50kg bag"
}
```

**Response**:
```json
{
  "success": true,
  "product_code": "CEMENT-50KG",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

---

### Example 2: Product with Excise Duty

**Request**:
```http
POST /api/external/efris/register-product
X-API-Key: efris_opVNle8KcO92KlXshJ1sSRT30y61sn3SKl3ExUv83Vw
Content-Type: application/json

{
  "item_code": "BEER-500ML",
  "item_name": "Domestic Beer 500ml",
  "unit_price": 3500,
  "commodity_code": "50101000",
  "unit_of_measure": "106",
  "have_excise_tax": "101",
  "excise_duty_code": "LED040100",
  "stock_quantity": 200,
  "description": "Locally produced beer, 500ml bottle"
}
```

**Response**:
```json
{
  "success": true,
  "product_code": "BEER-500ML",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

---

### Example 3: Service

**Request**:
```http
POST /api/external/efris/register-product
X-API-Key: efris_opVNle8KcO92KlXshJ1sSRT30y61sn3SKl3ExUv83Vw
Content-Type: application/json

{
  "item_code": "CONSULT-ACC",
  "item_name": "Accounting Consultation Service",
  "unit_price": 150000,
  "commodity_code": "80100000",
  "unit_of_measure": "110",
  "have_excise_tax": "102",
  "description": "Professional accounting and tax consultation"
}
```

**Response**:
```json
{
  "success": true,
  "product_code": "CONSULT-ACC",
  "efris_status": "Registered",
  "message": "Product registered successfully"
}
```

---

## Error Handling

### Common Errors

#### 1. Missing Required Field
```json
{
  "detail": "Missing required field: commodity_code"
}
```
**Fix**: Ensure all required fields are present.

---

#### 2. Invalid API Key
```json
{
  "detail": "Invalid or missing API key"
}
```
**Fix**: Check X-API-Key header.

---

#### 3. Excise Code Missing When Required
```json
{
  "detail": "excise_duty_code is required when have_excise_tax is 101"
}
```
**Fix**: Provide excise duty code when `have_excise_tax` = "101".

---

#### 4. EFRIS Server Error
```json
{
  "detail": "EFRIS returned error: Invalid commodity code"
}
```
**Fix**: Verify commodity code is valid and exists in EFRIS.

---

## EFRIS Field Mappings

Complete mapping between your ERP, our API, and EFRIS:

| Your ERP | Our API | EFRIS T130 | Notes |
|----------|---------|------------|-------|
| `sku` or `product_code` | `item_code` | `goodsCode` | Unique identifier (max 50 chars) |
| `name` or `item_name` | `item_name` | `goodsName` | Display name (max 200 chars) |
| `selling_price` | `unit_price` | `unitPrice` | Sent as string |
| `uom` or `unit` | `unit_of_measure` | `measureUnit` | 3-digit code from T115 |
| `commodity_category` | `commodity_code` | `commodityCategoryId` | EFRIS category ID (max 18 chars) |
| `has_excise` | `have_excise_tax` | `haveExciseTax` | "101" or "102" |
| `excise_code` | `excise_duty_code` | `exciseDutyCode` | When applicable |
| `description` or `notes` | `description` | `description` | Optional notes (max 1024 chars) |
| `reorder_level` | `stock_quantity` | `stockPrewarning` | Low stock threshold |
| - | - | `currency` | Always "101" (UGX) |
| - | - | `operationType` | Always "101" (Add) |
| - | - | `goodsTypeCode` | "101" (Goods) or "102" (Fuel) |
| - | - | `havePieceUnit` | Always "102" (No) - simplified |
| - | - | `pieceMeasureUnit` | Equal to measureUnit |
| - | - | `pieceUnitPrice` | Equal to unitPrice |
| - | - | `packageScaledValue` | Always "1" |
| - | - | `pieceScaledValue` | Always "1" |

---

## Implementation Checklist

### ✅ ERP Database Schema

- [ ] `sku` field (string, unique)
- [ ] `name` field (string, required)
- [ ] `sellingPrice` field (decimal)
- [ ] `commodityCode` field (string, 10 chars)
- [ ] `unitOfMeasure` field (string, 3 chars)
- [ ] `hasExciseDuty` field (boolean)
- [ ] `exciseDutyCode` field (string, nullable)
- [ ] `exciseDutyName` field (string, nullable, for display)
- [ ] `efrisRegistered` field (boolean, tracks sync status)

### ✅ UI Components

- [ ] Product/service form with all required fields
- [ ] Commodity code selector/dropdown
- [ ] Unit of measure selector
- [ ] Excise duty checkbox
- [ ] Excise code selector (appears when checkbox checked)
- [ ] Search/filter for excise codes

### ✅ Business Logic

- [ ] Product code generation logic implemented
- [ ] Field validation before API call
- [ ] Error handling for API failures
- [ ] Success/failure notifications
- [ ] Sync status tracking

### ✅ Integration

- [ ] API key securely stored
- [ ] Fetch excise codes on form load
- [ ] Register products immediately on creation
- [ ] OR batch register existing products
- [ ] Update EFRIS when product details change

---

## Testing Scenarios

### Test Case 1: Simple Product
- Create product WITHOUT excise duty
- Verify registration succeeds
- Check product appears in EFRIS

### Test Case 2: Excise Product
- Create product WITH excise duty
- Select excise code
- Verify registration succeeds
- Verify excise code is saved

### Test Case 3: Service
- Create service item
- Set unit_of_measure = "110"
- Verify registration succeeds

### Test Case 4: Product Code Logic
- Create product without SKU
- Verify code is derived from description or name
- Check sanitization works correctly

### Test Case 5: Error Handling
- Submit incomplete data
- Verify error messages are clear
- Check user can correct and resubmit

---

## Support & Questions

For integration support:
- Email: support@efrisintegration.com
- Documentation: https://efrisintegration.nafacademy.com/docs

---

**Last Updated**: February 8, 2026  
**API Version**: 1.0  
**EFRIS Interface**: T130 (Upload Goods)
