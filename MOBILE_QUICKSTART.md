# 📱 Mobile Features - Quick Reference

## URLs

### Desktop Dashboards (Now Mobile-Responsive)
- **Owner Portal:** `http://localhost:8001/static/owner_portal.html`
- **Multi-Tenant Dashboard:** `http://localhost:8001/static/dashboard_multitenant.html`
- **Reseller Portal:** `http://localhost:8001/static/reseller_portal.html`

### Mobile-First Dashboard
- **Mobile Client:** `http://localhost:8001/static/mobile_client.html`
  - Optimized for phones (320px - 768px)
  - Touch-friendly interface
  - Bottom navigation
  - Offline support

---

## Installation Instructions

### 📱 Install on Android

1. Open dashboard in **Chrome** or **Edge**
2. Tap **menu (⋮)** → **"Install app"**
3. Confirm installation
4. App icon appears on home screen
5. **Launch** from home screen

### 🍎 Install on iOS

1. Open dashboard in **Safari**
2. Tap **Share button (⬆️)**
3. Tap **"Add to Home Screen"**
4. Name the app → **"Add"**
5. App icon appears on home screen
6. **Launch** from home screen

### 💻 Install on Desktop

1. Open dashboard in **Chrome** or **Edge**
2. Look for **install icon (+)** in address bar
3. Click **"Install"**
4. App opens in standalone window
5. Pin to taskbar for quick access

---

## Features by Device

### 📱 **Mobile Phone (< 768px)**

✅ **Bottom Navigation**
- Home, Invoices, New, Products, Settings
- Easy thumb access
- Active state highlighting

✅ **Touch-Optimized**
- Large buttons (min 44x44px)
- Swipe gestures
- Pull-to-refresh
- Tap animations

✅ **Simplified Layout**
- Single column
- Card-based design
- Sticky header
- Floating action button

✅ **Offline Mode**
- View cached invoices
- Create new invoices
- Auto-sync when online
- Offline indicator banner

### 📱 **Tablet (768px - 1024px)**

✅ **Adaptive Layout**
- 2-column grids
- Collapsible sidebar
- Optimized tables
- Split-screen friendly

✅ **Enhanced Navigation**
- Horizontal navigation
- Quick actions
- Breadcrumbs
- Tab bars

### 💻 **Desktop (> 1024px)**

✅ **Full Experience**
- Sidebar navigation
- Multi-column layouts
- All features visible
- Keyboard shortcuts

---

## Quick Actions

### Create Invoice (Mobile)
1. Tap **"+"** button (center of bottom nav)
2. Fill form:
   - Customer name
   - TIN
   - Product (dropdown)
   - Quantity
   - Price
3. Tap **"Submit Invoice"**
4. Confirmation message

### View Invoices
1. Tap **"Invoices"** in bottom nav
2. Scroll through list
3. Tap invoice to view details
4. Status indicators:
   - 🟢 **Approved** (green)
   - 🟡 **Pending** (amber)
   - 🔴 **Rejected** (red)

### Search Products
1. Tap **"Products"** in bottom nav
2. Browse product list
3. See prices and availability
4. Tap to use in invoice

---

## Offline Capabilities

### ✅ **Works Offline:**
- View cached invoices
- Create new invoices (saved locally)
- Browse products
- View dashboard stats
- Search history

### ❌ **Requires Internet:**
- Submit to EFRIS
- Real-time sync
- Fresh statistics
- API updates

### 🔄 **Auto-Sync:**
When you come back online:
1. Offline banner disappears
2. "Syncing..." message shows
3. All pending invoices submit
4. Dashboard refreshes
5. "Sync complete!" message

---

## Notifications

### Setup:
1. Go to **Settings** tab
2. Tap **"Enable"** under Notifications
3. Allow in browser prompt
4. ✅ You'll receive:
   - Invoice approval notifications
   - EFRIS status updates
   - Sync completion alerts

### Types:
- 📨 **Invoice Approved** - Green badge
- ⏱ **Invoice Pending** - Amber badge
- ❌ **Invoice Rejected** - Red badge
- 🔄 **Sync Complete** - Blue badge

---

## Gestures

### Pull-to-Refresh
- Pull down from top of page
- Release when refresh icon appears
- Dashboard reloads data
- Works on all pages

### Swipe to Go Back
- Swipe right edge → go back
- Browser-native gesture
- Works in installed app

### Long Press
- Long press invoice → options menu
- Long press product → details
- Long press setting → info

---

## Status Indicators

### Connection Status (Top Right)
- 🟢 **Green dot:** Online
- 🔴 **Red dot:** Offline

### Sync Status
- ↻ **Spinning:** Syncing
- ✓ **Checkmark:** Synced
- ⚠️ **Warning:** Pending sync

### Banner Messages
- 🔵 **Blue:** Information
- 🟢 **Green:** Success
- 🟡 **Amber:** Warning
- 🔴 **Red:** Error

---

## Performance Tips

### Faster Loading:
1. ✅ **Install as app** (loads faster)
2. ✅ **Enable offline mode**
3. ✅ **Cache cleared regularly** (Settings)
4. ✅ **Update when prompted**

### Battery Saving:
1. Close app when not in use
2. Disable push notifications if not needed
3. Use WiFi instead of mobile data
4. Reduce screen brightness

### Data Usage:
- **First Load:** ~500KB (downloads app)
- **Daily Use:** ~50KB (API calls only)
- **Offline Use:** 0KB (no data used)

---

## Troubleshooting

### App won't install
**Android:**
- Update Chrome to latest version
- Check storage space
- Enable "Install from unknown sources"

**iOS:**
- Must use Safari (not Chrome)
- Update iOS to 14.0+
- Check storage space

### Not loading offline
- Open app once while online (initial cache)
- Check service worker is active:
  1. Chrome: menu → More tools → Developer tools
  2. Application tab → Service Workers
  3. Should show "activated and running"

### Sync not working
- Check internet connection
- Pull down to refresh
- Re-login if token expired
- Clear cache and reload

### Notifications not appearing
- Check permission granted in browser settings
- Enable notifications in Settings tab
- Test with "Send Test Notification" button

---

## Keyboard Shortcuts (Desktop)

| Shortcut | Action |
|----------|--------|
| `N` | New invoice |
| `I` | View invoices |
| `P` | View products |
| `/` | Search |
| `R` | Refresh |
| `Esc` | Close modal |
| `?` | Help |

---

## Accessibility

✅ **Screen Reader Support**
- All buttons labeled
- Status announcements
- Form field descriptions

✅ **Keyboard Navigation**
- Tab through forms
- Enter to submit
- Arrow keys for lists

✅ **Visual**
- High contrast mode
- Large touch targets
- Color-blind friendly icons

✅ **Motor**
- No required gestures
- Button alternatives
- Voice input supported

---

## Data Privacy

### What's Stored Locally:
- 📄 Cached invoices (for offline viewing)
- 🔑 API key (encrypted)
- ⚙️ User preferences
- 📊 Recent statistics

### What's Not Stored:
- ❌ Passwords
- ❌ Full customer database
- ❌ Payment information
- ❌ EFRIS credentials

### On Logout:
- All local data cleared
- Cache emptied
- Tokens removed
- Service worker stops

---

## Updates

### Automatic Updates:
- App checks for updates on launch
- Downloads in background
- Prompts to refresh when ready
- No manual update needed

### Manual Update:
1. Pull down to refresh
2. Or close and reopen app
3. New version loads automatically

### Update Notifications:
- 🔵 "Update available"
- Tap to reload
- Changes listed
- "What's new" screen

---

## Browser Compatibility

### ✅ **Fully Supported:**
| Browser | Version | Features |
|---------|---------|----------|
| Chrome (Android) | 90+ | All features |
| Chrome (Desktop) | 90+ | All features |
| Edge (Desktop) | 90+ | All features |
| Safari (iOS) | 14+ | All features* |
| Safari (macOS) | 14+ | All features* |

*iOS Safari has limited push notification support

### ⚠️ **Limited Support:**
| Browser | Version | Notes |
|---------|---------|-------|
| Firefox | 90+ | No install prompt (still works) |
| Samsung Internet | Latest | PWA works, some features limited |

### ❌ **Not Supported:**
- Internet Explorer (any version)
- Opera Mini
- Old Android Browser
- UC Browser

---

## Data Sync Schedule

### Real-Time:
- Invoice submissions
- Status updates
- New products

### Background (every 5 min):
- Statistics refresh
- Notification check

### On Demand:
- Pull-to-refresh
- Manual sync button
- App reopen

---

## Security Features

✅ **HTTPS Only**
- Encrypted connection
- Secure data transfer

✅ **Token-Based Auth**
- No passwords stored
- Auto-logout on token expiry
- Refresh tokens

✅ **Offline Security**
- Local data encrypted
- Cleared on logout
- No sensitive data cached

✅ **API Security**
- Rate limiting
- IP whitelisting
- 2FA support

---

## Best Practices

### For Daily Use:
1. ✅ Keep app installed on home screen
2. ✅ Enable notifications
3. ✅ Pull-to-refresh regularly
4. ✅ Create invoices in batches
5. ✅ Review dashboard daily

### For Offline Work:
1. ✅ Open app while online (initial cache)
2. ✅ Create invoices as normal
3. ✅ They save locally automatically
4. ✅ Connect to WiFi to sync
5. ✅ Verify sync completed (green checkmark)

### For Best Performance:
1. ✅ Update app when prompted
2. ✅ Clear old invoices monthly
3. ✅ Use WiFi for large syncs
4. ✅ Restart app if slow

---

## Support

### In-App Help:
- Tap **"?"** icon
- Settings → Help & Support
- Contact form

### Documentation:
- `/MOBILE_OPTIMIZATION_GUIDE.md` - Full guide
- `/MOBILE_QUICKSTART.md` - This guide
- API documentation

### Contact:
- Email: support@yourcompany.com
- Phone: +256-XXX-XXX-XXX
- Hours: Mon-Fri 8AM-6PM EAT

---

## Version Info

- **Mobile Client:** v1.0.0
- **PWA Support:** ✅ Enabled
- **Offline Mode:** ✅ Enabled
- **Last Updated:** February 6, 2026

---

**Happy mobile invoicing! 📱✨**
