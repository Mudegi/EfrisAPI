# 📹 EFRIS API - Video Tutorial Scripts

Scripts for creating video tutorials on common tasks. Each script includes:
- Duration estimate
- Required materials
- Step-by-step instructions with screen actions
- Narration text

---

## 📋 Tutorial List

1. [Getting Started - First Invoice (10 min)](#tutorial-1-getting-started---first-invoice)
2. [Setting Up API Integration (8 min)](#tutorial-2-setting-up-api-integration)
3. [Product Registration (5 min)](#tutorial-3-product-registration)
4. [Handling Errors (7 min)](#tutorial-4-handling-errors)
5. [Mobile Dashboard Setup (6 min)](#tutorial-5-mobile-dashboard-setup)
6. [Custom ERP Integration (15 min)](#tutorial-6-custom-erp-integration)
7. [Excise Duty Invoices (8 min)](#tutorial-7-excise-duty-invoices)

---

## Tutorial 1: Getting Started - First Invoice

**Duration**: 10 minutes  
**Difficulty**: Beginner  
**Requirements**: Account credentials, sample product

### Video Script

#### Scene 1: Introduction (0:00 - 0:30)
```
[SCREEN: Show landing page]

NARRATOR:
"Welcome to the EFRIS API platform! In this tutorial, 
you'll learn how to submit your first invoice to Uganda 
Revenue Authority's EFRIS system in under 10 minutes.

By the end of this video, you'll have successfully 
submitted an invoice and received your Fiscal Document 
Number."

[GRAPHICS: Show FDN example, QR code]
```

#### Scene 2: Login (0:30 - 1:30)
```
[SCREEN: Navigate to login page]

NARRATOR:
"First, let's log into your dashboard."

[ACTION: Type URL in browser]
1. Open browser
2. Navigate to: efrisintegration.nafacademy.com
3. Click "Login"

[SCREEN: Login form appears]

[ACTION: Fill login form]
4. Enter your email
5. Enter password
6. Click "Sign In"

[SCREEN: Dashboard loads]

NARRATOR:
"Great! You're now in your dashboard where you can see 
all your invoice statistics."

[GRAPHICS: Highlight key dashboard elements]
```

#### Scene 3: Dashboard Overview (1:30 - 2:30)
```
[SCREEN: Dashboard view]

NARRATOR:
"Let's quickly tour the dashboard."

[ACTION: Hover over each element as explained]

"On the left, you'll see your total invoices, successful 
submissions, and any pending items.

In the center, there's a graph showing your submission 
activity over time.

And here on the right, your recent invoices with their 
status."

[GRAPHICS: Annotate each section]
```

#### Scene 4: Creating First Invoice (2:30 - 6:00)
```
[SCREEN: Click "New Invoice" button]

NARRATOR:
"Now let's create your first invoice. Click the 'New Invoice' 
button in the top right."

[SCREEN: Invoice form appears]

NARRATOR:
"The form is divided into sections. Let's fill each one."

[ACTION: Fill Seller Details]

1. Seller Details (already pre-filled with your info)
   "These are automatically filled from your profile."

2. Invoice Information
   [TYPE] Invoice Number: INV-001
   [TYPE] Date: [Today's date]
   [SELECT] Currency: UGX
   
   NARRATOR:
   "Enter a unique invoice number - this must be different 
   for every invoice. The date defaults to today."

3. Buyer Details
   [TYPE] Buyer Name: ABC Company Ltd
   [TYPE] TIN: 1000000000 (if B2B)
   [TYPE] Phone: 0700123456
   
   NARRATOR:
   "For B2B transactions, the buyer's TIN is required. 
   For B2C, you can leave it empty."

4. Add Product
   [CLICK] "Add Product" button
   [TYPE] Description: Office Chair
   [TYPE] Quantity: 1
   [TYPE] Unit Price: 300000
   [SELECT] Tax Rate: 18%
   
   NARRATOR:
   "Enter your product details. The system will 
   automatically calculate the tax and total."
   
   [SCREEN: Show calculated totals]
   
   "See? The net amount, tax, and gross amount are 
   calculated automatically."

5. Review Summary
   [SCREEN: Summary section highlights]
   
   NARRATOR:
   "Always review the summary before submitting. 
   Make sure all amounts are correct."
```

#### Scene 5: Submit Invoice (6:00 - 7:30)
```
[SCREEN: Click "Submit to EFRIS" button]

NARRATOR:
"When you're ready, click 'Submit to EFRIS'."

[SCREEN: Loading spinner]

NARRATOR:
"The system now encrypts your invoice, signs it with your 
digital certificate, and sends it securely to URA's EFRIS 
system."

[SCREEN: Success message appears]

NARRATOR:
"Success! Your invoice has been submitted."

[SCREEN: Show FDN and QR code]

NARRATOR:
"You've received your Fiscal Document Number - this is your 
proof of submission to URA. 

The QR code can be printed on your receipt for customer 
verification."

[ACTION: Click "Download PDF"]

NARRATOR:
"You can download a PDF copy for your records."
```

#### Scene 6: Verify Submission (7:30 - 9:00)
```
[SCREEN: Navigate to "Invoices" tab]

NARRATOR:
"To see all your invoices, click the 'Invoices' tab."

[SCREEN: Invoice list showing new invoice]

[ACTION: Click on recent invoice]

NARRATOR:
"Here's your invoice with all the details. The status 
shows 'Approved' meaning EFRIS has accepted it.

You can see the submission timestamp, FDN, and even 
reprint the invoice anytime."

[GRAPHICS: Highlight key fields]
```

#### Scene 7: Next Steps (9:00 - 10:00)
```
[SCREEN: Dashboard view]

NARRATOR:
"Congratulations! You've successfully submitted your 
first invoice to EFRIS.

Here's what to do next:

1. Register more products in the Products section
2. Set up automated integration using our API
3. Configure multiple users if needed

For more tutorials, check our documentation or contact 
support."

[GRAPHICS: Show links to resources]

[SCREEN: End card with contact info]

NARRATOR:
"Thanks for watching! Don't forget to subscribe for 
more tutorials."
```

---

## Tutorial 2: Setting Up API Integration

**Duration**: 8 minutes  
**Difficulty**: Intermediate  
**Requirements**: Programming knowledge, API key

### Video Script

#### Scene 1: Introduction (0:00 - 0:30)
```
[SCREEN: Code editor with API logo]

NARRATOR:
"In this tutorial, we'll integrate EFRIS with your 
existing system using our REST API.

You'll learn how to:
- Generate an API key
- Make your first API call
- Submit an invoice programmatically
- Handle responses and errors"

[GRAPHICS: Show API flow diagram]
```

#### Scene 2: Generate API Key (0:30 - 2:00)
```
[SCREEN: Dashboard → Settings]

NARRATOR:
"First, let's generate your API key."

[ACTION: Navigate to settings]
1. Click your profile icon
2. Select "Settings"
3. Click "API Keys" tab

[SCREEN: API Keys page]

[ACTION: Generate key]
4. Click "Generate New API Key"
5. Enter description: "Production Server"
6. Set expiration: 1 year
7. Click "Generate"

[SCREEN: API key shown]

NARRATOR:
"Important! Copy this key now. You won't see it again.

Store it securely in your environment variables, 
never commit it to version control."

[GRAPHICS: Show correct storage methods]

[COPY KEY TO CLIPBOARD ANIMATION]
```

#### Scene 3: Test API Connection (2:00 - 4:00)
```
[SCREEN: Code editor]

NARRATOR:
"Let's test the API connection. I'll use Python, 
but the same concepts apply to any language."

[TYPE CODE on screen:]

```python
import requests

# Your API key
API_KEY = "efris_abc123..."
BASE_URL = "https://efrisintegration.nafacademy.com/api"

# Test connection
response = requests.get(
    f"{BASE_URL}/dashboard/stats",
    headers={"X-API-Key": API_KEY}
)

print(response.status_code)  # Should be 200
print(response.json())
```

[RUN CODE]

[SCREEN: Console output showing 200 and JSON data]

NARRATOR:
"Perfect! A 200 status code means we're connected. 
You can see your dashboard statistics returned as JSON."

[GRAPHICS: Explain JSON structure]
```

#### Scene 4: Submit Invoice via API (4:00 - 6:30)
```
[SCREEN: Code editor]

NARRATOR:
"Now let's submit an invoice programmatically."

[TYPE CODE:]

```python
invoice_data = {
    "invoice_number": "API-INV-001",
    "invoice_date": "2026-02-06",
    "customer_name": "ABC Company",
    "customer_tin": "1000000000",
    "customer_phone": "0700123456",
    "items": [
        {
            "description": "Laptop Computer",
            "quantity": 1,
            "unit_price": 2500000,
            "tax_rate": 18
        }
    ]
}

# Submit to EFRIS
response = requests.post(
    f"{BASE_URL}/external/efris/submit-invoice",
    json=invoice_data,
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Success! FDN: {result['fdn']}")
    print(f"QR Code: {result['qr_code']}")
else:
    print(f"Error: {response.json()}")
```

[RUN CODE]

[SCREEN: Success output with FDN]

NARRATOR:
"Excellent! The invoice was submitted successfully. 
You received the FDN and QR code in the response.

You can now save these to your database and print 
them on your receipt."
```

#### Scene 5: Error Handling (6:30 - 7:30)
```
[SCREEN: Code editor]

NARRATOR:
"Let's add proper error handling for production use."

[TYPE CODE:]

```python
def submit_invoice_safely(invoice_data):
    try:
        response = requests.post(
            f"{BASE_URL}/external/efris/submit-invoice",
            json=invoice_data,
            headers={"X-API-Key": API_KEY},
            timeout=30
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 401:
            return {"success": False, "error": "Invalid API key"}
        elif response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded"}
        else:
            return {"success": False, "error": response.json()}
            
    except requests.Timeout:
        return {"success": False, "error": "Request timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

NARRATOR:
"This handles common errors like invalid keys, rate limits, 
and timeouts gracefully."
```

#### Scene 6: Conclusion (7:30 - 8:00)
```
[SCREEN: Summary slide]

NARRATOR:
"You've now integrated EFRIS with your system!

Key takeaways:
1. Always secure your API key
2. Handle errors gracefully
3. Store FDN for compliance
4. Monitor rate limits

Full documentation available at docs.efrisintegration.com

Thanks for watching!"
```

---

## Tutorial 3: Product Registration

**Duration**: 5 minutes  
**Difficulty**: Beginner

### Video Script

#### Scene 1: Introduction (0:00 - 0:30)
```
NARRATOR:
"Before you can invoice products, you need to register 
them with EFRIS.

In this quick tutorial, you'll learn how to:
- Register new products
- Choose correct category codes
- Handle product variations"
```

#### Scene 2: Navigate to Products (0:30 - 1:00)
```
[SCREEN: Dashboard → Products]

[ACTION: Click "Products" in sidebar]

NARRATOR:
"From your dashboard, click 'Products' in the left menu."

[SCREEN: Products list (empty or with few items)]
```

#### Scene 3: Add New Product (1:00 - 3:30)
```
[SCREEN: Click "Add Product" button]

NARRATOR:
"Click 'Add Product' to create a new item."

[SCREEN: Product form]

[ACTION: Fill form]

1. Product Code: CHAIR-001
   NARRATOR: "Use a unique code for inventory management"

2. Description: Ergonomic Office Chair
   NARRATOR: "Clear description for EFRIS records"

3. Unit of Measure: Piece (PCS)
   NARRATOR: "Select from standard units"

4. Unit Price: 300,000 UGX
   NARRATOR: "Your selling price before tax"

5. Tax Rate: 18%
   NARRATOR: "Standard VAT rate in Uganda"

6. Category: [Search] "Furniture"
   NARRATOR: "This is crucial - choose the correct EFRIS category"
   
   [SCREEN: Category dropdown shows options]
   
   Select: 1010101010104 - Office Furniture
   
   NARRATOR: "Each category has a 13-digit code. The system 
   helps you find the right one."

7. Click "Register with EFRIS"

[SCREEN: Loading, then success]

NARRATOR:
"Your product is now registered with URA and ready to use 
in invoices!"
```

#### Scene 4: Managing Products (3:30 - 4:30)
```
[SCREEN: Products list with new product]

NARRATOR:
"Your products are now listed here. You can:

- Edit products (click pencil icon)
- View registration status
- Search and filter

Once registered, use these products in any invoice."

[DEMO: Create invoice and select registered product]
```

#### Scene 5: Conclusion (4:30 - 5:00)
```
NARRATOR:
"That's it! Product registration in under 5 minutes.

Pro tips:
- Register products before busy periods
- Use consistent naming conventions
- Keep categories accurate

See you in the next tutorial!"
```

---

## Tutorial 4: Handling Errors

**Duration**: 7 minutes  
**Difficulty**: Intermediate

### Video Script

#### Scene 1: Common Errors (0:00 - 2:00)
```
[SCREEN: Show error message]

NARRATOR:
"Errors happen. Let's learn how to diagnose and fix 
the most commoncases.

Today we'll cover:
- Missing field errors
- Tax calculation errors  
- Duplicate invoice errors
- Network timeouts"

[GRAPHICS: Show error categories]
```

#### Scene 2: Missing Field Error (2:00 - 3:30)
```
[SCREEN: Submit invoice with missing field]

[ACTION: Try to submit]

[SCREEN: Error appears: "Missing required field: buyerTin"]

NARRATOR:
"This is a B2B transaction, so buyer TIN is required."

[ACTION: Add TIN and resubmit]

[SCREEN: Success]

NARRATOR:
"The error message tells you exactly what's missing. 
Always read it carefully before asking for help."

[GRAPHICS: Show required fields checklist]
```

#### Scene 3-4: [Continue with other error types...] 

---

## Tutorial 5: Mobile Dashboard Setup

**Duration**: 6 minutes  
**Difficulty**: Beginner

### Video Script

```
[Full script for PWA installation on mobile devices]
- Opening website on phone
- "Add to Home Screen" prompt
- Using offline features
- Mobile invoice submission
```

---

## Tutorial 6: Custom ERP Integration

**Duration**: 15 minutes  
**Difficulty**: Advanced

### Video Script

```
[Detailed integration guide]
- Webhook setup
- Real-time sync
- Error recovery
- Testing integration
```

---

## Tutorial 7: Excise Duty Invoices

**Duration**: 8 minutes  
**Difficulty**: Intermediate

### Video Script

```
[Excisable goods handling]
- Identifying excisable products
- Adding excise codes
- Tax calculation with excise
- Submission and verification
```

---

## 📝 Recording Tips

### Equipment Needed:
- Screen recording software (OBS Studio, Camtasia)
- Microphone (at least USB quality)
- Video editing software
- Graphic templates for annotations

### Recording Best Practices:
1. **Preparation**:
   - Test all steps beforehand
   - Clear browser cache/cookies
   - Use sample data (not real customer info)
   - Close unnecessary applications

2. **During Recording**:
   - Speak clearly and slowly
   - Pause between sections (easier to edit)
   - Show mouse clicks clearly
   - Allow time for pages to load

3. **Post-Production**:
   - Add captions/subtitles
   - Speed up slow sections (loading screens)
   - Add background music (low volume)
   - Include chapter markers

### Branding:
- Use consistent intro/outro
- Add logo watermark
- Include social media links
- Show URL on screen when mentioned

---

## 📤 Publishing Checklist

- [ ] Upload to YouTube
- [ ] Create thumbnail (1280x720)
- [ ] Write description with timestamps
- [ ] Add tags (EFRIS, URA, Uganda, Invoice, API)
- [ ] Add to playlist
- [ ] Link in documentation
- [ ] Share on social media
- [ ] Pin important comment

---

**Ready to record?** Use these scripts as your guide and feel free to adapt based on your style and audience!
