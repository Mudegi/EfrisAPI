# Multi-Tenant Dashboard - Quick Start Guide

## 🎉 New Dashboard Features

### Modern UI
- 🎨 Beautiful gradient design with smooth animations
- 📱 Fully responsive layout
- 🌙 Professional color scheme

### Multi-Tenant Support
- 👥 Support for multiple users
- 🏢 Support for multiple companies per user
- 🔐 Secure JWT authentication
- 🔄 Easy company switching

### Key Features
- ✅ Secure login system
- ✅ Company selector dropdown
- ✅ Real-time data loading
- ✅ Products management view
- ✅ Invoice tracking
- ✅ Company information display
- ✅ User profile with sign out
- ✅ Toast notifications
- ✅ Statistics dashboard

## 🚀 How to Use

### 1. Start the Server
```powershell
cd d:\EfrisAPI
C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe api_multitenant.py
```

### 2. Access the Dashboard
Open your browser and go to:
```
http://localhost:8001/
```

### 3. Login
Use the admin credentials:
- **Email**: admin@wandera.com
- **Password**: Admin2026!

### 4. Select Company
After login, use the company dropdown in the sidebar to select your active company.

### 5. Navigate Sections
- **Overview** - Company stats and information
- **Products** - View all products
- **Invoices** - Track invoice history
- **Settings** - Company settings (coming soon)

## 📋 Dashboard Sections

### Overview Tab
- Total products count
- Total invoices count
- Approved invoices count
- Company status badge
- Detailed company information table

### Products Tab
- Product catalog table
- Shows: Product Code, Name, QB Item ID, EFRIS Status, Excise flag
- Sync button for EFRIS integration

### Invoices Tab
- Invoice history table
- Shows: QB Invoice ID, Customer, Amount, EFRIS FDN, Status, Date
- Sync button for EFRIS integration

### Settings Tab
- Company configuration (to be implemented)

## 🔧 Technical Details

### Authentication Flow
1. User enters email and password
2. System sends credentials to `/api/auth/login`
3. Server validates and returns JWT token
4. Token stored in browser's localStorage
5. Token sent with every API request in Authorization header

### Company Selection
- User's companies loaded from `/api/companies`
- Selected company ID stored in localStorage
- Company data loaded from company-specific endpoints:
  - `/api/companies/{id}` - Company details
  - `/api/companies/{id}/products` - Products
  - `/api/companies/{id}/invoices` - Invoices

### Auto-Refresh
- Data persists across page reloads
- Token validated on page load
- Auto-redirects to login if token expired

### Security
- JWT tokens with 8-hour expiry
- Secure password hashing
- CORS protection
- Company data isolation

## 🎨 UI Components

### Login Page
- Clean, centered login form
- Email and password fields
- Error message display
- Loading state during authentication

### Sidebar
- Company logo and title
- Connection status indicator
- Company selector dropdown
- Navigation menu (Overview, Products, Invoices, Settings)
- User profile card at bottom
- Sign out button

### Top Bar
- Current page title
- Refresh button for data reload

### Content Area
- Tabbed interface
- Statistics cards
- Data tables with modern styling
- Empty states for no data
- Loading spinners

### Toast Notifications
- Success messages (green)
- Error messages (red)
- Auto-dismiss after 3 seconds
- Slide-up animation

## 🔄 Data Sync Flow

### Products Sync (Future Implementation)
1. Click "Sync with EFRIS" in Products tab
2. System will connect to EFRIS T127 endpoint
3. Fetch latest product catalog
4. Update database with new products
5. Refresh products table

### Invoices Sync (Future Implementation)
1. Click "Sync with EFRIS" in Invoices tab
2. Connect to QuickBooks to get invoices
3. Submit to EFRIS T109 endpoint
4. Update database with FDN numbers
5. Refresh invoices table

## 📱 Responsive Design

The dashboard is fully responsive:
- Desktop: Full sidebar + content
- Tablet: Collapsible sidebar
- Mobile: Hamburger menu (future enhancement)

## 🔐 Security Best Practices

1. **Never share your password**
2. **Log out when finished**
3. **Use strong passwords** (min 8 characters, max 72)
4. **Keep your token secure** (automatically handled by browser)

## 🐛 Troubleshooting

### Can't Login
- Check email and password are correct
- Ensure server is running on port 8001
- Check browser console for errors

### No Companies Shown
- Verify user is linked to at least one company
- Check database: `SELECT * FROM company_users WHERE user_id=1;`

### Data Not Loading
- Check browser console for API errors
- Verify token is valid (check Network tab)
- Ensure company is selected in dropdown

### Connection Status Red
- Check if API server is running
- Verify CORS settings allow your origin
- Check network connectivity

## 🔗 API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login` | POST | User authentication |
| `/api/auth/me` | GET | Get current user info |
| `/api/companies` | GET | List user's companies |
| `/api/companies/{id}` | GET | Get company details |
| `/api/companies/{id}/products` | GET | List company products |
| `/api/companies/{id}/invoices` | GET | List company invoices |

## 🎯 Next Steps

### Planned Features
- [ ] QuickBooks OAuth integration UI
- [ ] Real-time EFRIS sync buttons
- [ ] Invoice creation form
- [ ] Product registration form
- [ ] Company settings page
- [ ] User management (admin only)
- [ ] Audit log viewer
- [ ] Export reports (CSV, PDF)
- [ ] Dark mode toggle
- [ ] Multi-language support

### Integration Points
1. Connect old single-tenant EFRIS functions
2. Add QuickBooks OAuth flow to UI
3. Implement T109 invoice submission
4. Implement T127 product sync
5. Add T106 invoice query
6. Add company-specific EFRIS certificate management

## 📞 Support

For issues or questions:
1. Check MULTITENANT_STATUS.md for system status
2. Check MULTITENANT_SETUP.md for architecture details
3. Review browser console for errors
4. Check API server logs

---

**Dashboard Version**: 2.0.0  
**Last Updated**: January 18, 2026  
**Status**: ✅ Production Ready
