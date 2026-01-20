# Search Functionality - Control Panel ✅

## Overview
All control panel modules now support search/filter functionality. Users can search across relevant fields in each module.

## Implementation

### Search Method
- **Type**: Case-insensitive partial match (SQL `ILIKE`)
- **Operator**: OR logic (matches any field)
- **Query Parameter**: `?search=keyword`

## Endpoints with Search

### 1. Products (`/api/companies/{company_id}/products`)
**Search Fields:**
- Product Name (`qb_name`)
- SKU (`qb_sku`)
- Description (`qb_description`)

**Example:**
```bash
GET /api/companies/1/products?search=spice
# Returns: All products with "spice" in name, SKU, or description
```

### 2. Invoices (`/api/companies/{company_id}/invoices`)
**Search Fields:**
- Document Number (`qb_doc_number`)
- Customer Name (`qb_customer_name`)

**Example:**
```bash
GET /api/companies/1/invoices?search=1044
# Returns: Invoices with doc number or customer name containing "1044"
```

### 3. EFRIS Goods (`/api/companies/{company_id}/efris-goods`)
**Search Fields:**
- Goods Code (`goods_code`)
- Goods Name (`goods_name`)

**Example:**
```bash
GET /api/companies/1/efris-goods?search=Fanta
# Returns: All EFRIS goods with "Fanta" in code or name
```

### 4. EFRIS Invoices (`/api/companies/{company_id}/efris-invoices`)
**Search Fields:**
- Invoice Number (`invoice_no`)
- Buyer Legal Name (`buyer_legal_name`)
- Buyer Business Name (`buyer_business_name`)

**Example:**
```bash
GET /api/companies/1/efris-invoices?search=Dylan
# Returns: EFRIS invoices with "Dylan" in invoice number or buyer names
```

### 5. QB Invoices (Database) (`/api/companies/{company_id}/qb-invoices`)
**Search Fields:**
- Document Number (`qb_doc_number`)
- Customer Name (`qb_customer_name`)

**Example:**
```bash
GET /api/companies/1/qb-invoices?search=Cool
# Returns: QB invoices with "Cool" in doc number or customer name
```

### 6. QB Purchase Orders (`/api/companies/{company_id}/qb-purchase-orders`)
**Search Fields:**
- Document Number (`qb_doc_number`)
- Vendor Name (`qb_vendor_name`)

**Example:**
```bash
GET /api/companies/1/qb-purchase-orders?search=Bob
# Returns: POs with "Bob" in doc number or vendor name
```

### 7. QB Items (`/api/companies/{company_id}/qb-items`)
**Search Fields:**
- Item Name (`qb_name`)
- SKU (`qb_sku`)
- Description (`qb_description`)

**Example:**
```bash
GET /api/companies/1/qb-items?search=service
# Returns: QB items with "service" in name, SKU, or description
```

### 8. Credit Memos (`/api/companies/{company_id}/qb-credit-memos`)
**Search Fields:**
- Document Number (`qb_doc_number`)
- Customer Name (`qb_customer_name`)

**Example:**
```bash
GET /api/companies/1/qb-credit-memos?search=Amy
# Returns: Credit memos with "Amy" in doc number or customer name
```

## UI Integration

### Frontend Implementation
Add a search input box to each module view:

```html
<input 
  type="text" 
  placeholder="Search..." 
  class="search-input"
  oninput="searchRecords(this.value)"
/>
```

```javascript
function searchRecords(keyword) {
  const url = `/api/companies/1/products?search=${encodeURIComponent(keyword)}`;
  fetch(url)
    .then(response => response.json())
    .then(data => {
      // Update table with filtered results
      updateTable(data);
    });
}
```

### Search Behavior
- **Empty search**: Returns all records (sorted by date)
- **With search term**: Returns filtered records (still sorted by date)
- **Case-insensitive**: "SPICE" = "spice" = "Spice"
- **Partial match**: "Fan" matches "Fanta 2025 500ml"

## Technical Details

### SQL Query Example
```python
# Without search
query = db.query(Product).filter(Product.company_id == company_id)

# With search
if search:
    search_pattern = f"%{search}%"
    query = query.filter(
        (Product.qb_name.ilike(search_pattern)) |
        (Product.qb_sku.ilike(search_pattern)) |
        (Product.qb_description.ilike(search_pattern))
    )

# Apply sorting
products = query.order_by(Product.updated_at.desc()).all()
```

### Performance Notes
- Uses database-level filtering (efficient)
- Indexes recommended on frequently searched fields
- OR operator used for multi-field search
- Sorting applied after filtering

## Testing

### Test Commands
```bash
# Test product search
curl "http://localhost:8001/api/companies/1/products?search=spice"

# Test invoice search by customer
curl "http://localhost:8001/api/companies/1/qb-invoices?search=Cool%20Cars"

# Test invoice search by doc number
curl "http://localhost:8001/api/companies/1/qb-invoices?search=1044"

# Test EFRIS goods search
curl "http://localhost:8001/api/companies/1/efris-goods?search=Fanta"

# Test PO search by vendor
curl "http://localhost:8001/api/companies/1/qb-purchase-orders?search=Bob"
```

## Server Status
✅ Server running on port 8001
✅ All search endpoints active
✅ Maintains sorting (newest first) with search results
