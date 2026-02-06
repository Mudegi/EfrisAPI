# 🎯 ADMIN SETTINGS MANAGEMENT GUIDE

## Overview

You now have a **complete settings management system** that allows you to update landing page content, contact information, and system configuration through an admin dashboard—no more hardcoding!

---

## 🚀 Quick Start

### 1. Access Settings Panel

1. **Login** as Owner or Admin at: `https://yourdomain.com/login`
2. Navigate to **⚙️ Settings** tab in the Owner Portal
3. All settings are displayed in a table

### 2. Update a Setting

1. Click **✏️ Edit** button next to any setting
2. Modify the value in the popup
3. Click **💾 Save Changes**
4. Landing page will automatically show new values!

---

## 📋 Available Settings Categories

### 📧 Contact Information
| Setting Key | Description | Example |
|------------|-------------|---------|
| `contact_email` | Support email address | support@company.com |
| `contact_phone` | Primary phone number | +256 700 123 456 |
| `contact_whatsapp` | WhatsApp number (no spaces) | 256700123456 |
| `contact_address` | Physical address | Kampala, Uganda |
| `business_hours` | Operating hours | Mon-Fri: 8AM-6PM (EAT) |

### 🔗 Social Media
| Setting Key | Description | Example |
|------------|-------------|---------|
| `social_twitter` | Twitter profile URL | https://twitter.com/yourcompany |
| `social_facebook` | Facebook page URL | https://facebook.com/yourcompany |
| `social_linkedin` | LinkedIn page URL | https://linkedin.com/company/yourcompany |

### 🏢 Company Information
| Setting Key | Description | Example |
|------------|-------------|---------|
| `company_name` | Your company name | EFRIS Integration Platform |
| `company_tagline` | Company tagline | Leading EFRIS solution in Uganda |
| `company_description` | Company description | Full description text... |

### 📊 Landing Page Stats
| Setting Key | Description | Example |
|------------|-------------|---------|
| `stat_companies` | Active companies count | 500+ |
| `stat_invoices` | Invoices fiscalized | 50K+ |
| `stat_uptime` | Uptime guarantee | 99.9% |

### 🎛️ Feature Flags
| Setting Key | Description | Values |
|------------|-------------|--------|
| `enable_registration` | Allow new registrations | 1 (on) / 0 (off) |
| `enable_api_docs` | Show API documentation | 1 (on) / 0 (off) |
| `maintenance_mode` | Enable maintenance mode | 1 (on) / 0 (off) |
| `maintenance_message` | Maintenance message | Text to show users |

### 💰 Pricing
| Setting Key | Description | Example |
|------------|-------------|---------|
| `trial_days` | Free trial days | 2 |
| `pricing_model` | Pricing model type | contact/fixed/tiered |

---

## 🔒 Public vs Private Settings

### Public Settings (✅ PUBLIC)
- **Displayed on landing page** to all visitors
- Fetched via `/api/settings/public` (no auth required)
- Examples: contact info, social links, stats

### Private Settings (🔒 PRIVATE)
- **Only visible to admins** in settings panel
- Require authentication to access
- Examples: email config, system settings, feature flags

---

## 🎨 How It Works

### Landing Page (Automatic)
1. When landing page loads, it calls `/api/settings/public`
2. JavaScript automatically replaces placeholders with real values
3. Contact info, social links, and stats are updated dynamically
4. **No need to edit HTML files anymore!**

### Admin Dashboard
1. Owner/Admin logs in to portal
2. Goes to **⚙️ Settings** tab
3. Edits any setting value
4. Changes are immediately saved to database
5. Landing page reflects changes on next page load

---

## 📝 Common Tasks

### Update Contact Phone Number

1. Login as owner
2. Go to **⚙️ Settings** tab
3. Filter by **📧 Contact Information**
4. Find `contact_phone` setting
5. Click **✏️ Edit**
6. Update value: `+256 700 123 456`
7. Click **💾 Save Changes**
8. ✅ Done! Landing page now shows new number

### Change Social Media Links

1. Go to **⚙️ Settings** tab
2. Filter by **🔗 Social Media**
3. Edit these settings:
   - `social_twitter` → Your Twitter URL
   - `social_facebook` → Your Facebook URL
   - `social_linkedin` → Your LinkedIn URL
4. Save each change
5. ✅ Social icons on landing page updated!

### Update Statistics

1. Go to **⚙️ Settings** tab
2. Filter by **📊 Statistics**
3. Update:
   - `stat_companies` → e.g., "1000+"
   - `stat_invoices` → e.g., "100K+"
   - `stat_uptime` → e.g., "99.9%"
4. Save changes
5. ✅ Stats section on landing page updated!

---

## 🔧 API Endpoints Reference

### Get Public Settings (No Auth)
```http
GET /api/settings/public
```
Returns all public settings as JSON

### Get All Settings (Admin Only)
```http
GET /api/settings/all
Authorization: Bearer {token}
```

### Get Settings by Category (Admin Only)
```http
GET /api/settings/category/contact
Authorization: Bearer {token}
```

### Update Setting (Admin Only)
```http
PUT /api/settings/{setting_key}
Authorization: Bearer {token}
Content-Type: application/json

{
  "setting_value": "new value"
}
```

### Create New Setting (Admin Only)
```http
POST /api/settings
Authorization: Bearer {token}
Content-Type: application/json

{
  "setting_key": "new_setting",
  "setting_value": "value",
  "setting_type": "text",
  "category": "general",
  "description": "Description",
  "is_public": 0
}
```

---

## 💡 Pro Tips

### Tip 1: Filter by Category
Use the category dropdown to view only specific types of settings:
- **📧 Contact Information** - Update all contact details
- **🔗 Social Media** - Manage all social links
- **📊 Statistics** - Update landing page numbers

### Tip 2: WhatsApp Link Format
For WhatsApp, use number without spaces or +: **256700123456**  
The system converts it to proper link format automatically.

### Tip 3: Refresh After Changes
Click **🔄 Refresh** button in settings panel to reload data after bulk changes.

### Tip 4: Test Changes
After updating settings:
1. Open landing page in new tab
2. Verify changes are visible
3. Check contact links work correctly

---

## 🆘 Troubleshooting

### Settings Not Loading
- **Check**: Are you logged in as owner/admin?
- **Try**: Refresh the page
- **Verify**: Browser console for errors (F12)

### Changes Not Showing on Landing Page
- **Refresh** the landing page (not just settings panel)
- **Clear cache**: Ctrl+F5 or Cmd+Shift+R
- **Check**: Is setting marked as PUBLIC (✅)?

### Cannot Edit Settings
- **Verify**: You have owner or admin role
- **Check**: Token is valid (re-login if needed)

### WhatsApp Link Not Working
- **Format**: Use 256700123456 (no + or spaces)
- **Update**: Both `contact_whatsapp` AND `contact_phone`

---

## 🎓 Example Workflow

### Complete Setup - Your First Login

1. **Login** to owner portal
2. **Navigate** to ⚙️ Settings tab
3. **Update Contact Info**:
   ```
   contact_email → your-email@company.com
   contact_phone → +256 700 123 456
   contact_whatsapp → 256700123456
   contact_address → Your City, Uganda
   ```
4. **Update Social Media**:
   ```
   social_twitter → https://twitter.com/yourcompany
   social_facebook → https://facebook.com/yourpage
   social_linkedin → https://linkedin.com/company/yourcompany
   ```
5. **Update Company Info**:
   ```
   company_name → Your Company Name
   company_tagline → Your Tagline
   ```
6. **Update Stats** (if needed):
   ```
   stat_companies → Current number
   stat_invoices → Current number
   ```
7. **Visit Landing Page** → Verify all changes!
8. **Test Links** → Click email, phone, social links
9. **Done!** ✅ Professional landing page with your info

---

## 📊 Database Structure

Settings are stored in `system_settings` table:
```
system_settings
├── id (primary key)
├── setting_key (unique)
├── setting_value
├── setting_type (text, email, url, textarea, boolean, number, password)
├── category (contact, social, company, stats, features, pricing, email, system)
├── description
├── is_public (0 or 1)
├── created_at
└── updated_at
```

---

## 🚀 Next Steps

1. **Login** to your owner portal
2. **Update** your contact information
3. **Customize** landing page content
4. **Test** all links and settings
5. **Share** your professional landing page!

---

## 📞 Need Help?

If you encounter any issues:
1. Check this guide first
2. Verify your role is owner/admin
3. Check browser console for errors
4. Contact system administrator

---

**Last Updated**: February 6, 2026  
**Version**: 1.0.0  
**Author**: EFRIS Integration Platform Team

---

**✨ That's it! No more hardcoded values—manage everything from the admin dashboard!**
