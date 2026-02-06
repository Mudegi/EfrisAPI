# PWA Icons Directory

This directory should contain all PWA icon files for the mobile app.

## Required Icon Sizes

Create PNG images at the following sizes:

- **icon-72x72.png** - Small Android icon
- **icon-96x96.png** - Android notification icon
- **icon-128x128.png** - Chrome Web Store
- **icon-144x144.png** - Windows tile
- **icon-152x152.png** - iOS app icon
- **icon-192x192.png** - Android home screen (primary)
- **icon-384x384.png** - Large icon
- **icon-512x512.png** - Splash screen (primary)

## Additional Assets

- **badge-72x72.png** - Notification badge
- **dashboard-96x96.png** - Dashboard shortcut icon
- **invoice-96x96.png** - Invoice shortcut icon
- **open-24x24.png** - Open action icon
- **close-24x24.png** - Close action icon

## How to Generate

### Option 1: Automated (Recommended)

```bash
# Install Pillow
pip install Pillow

# Generate from your logo (512x512 PNG recommended)
python ../../../generate_pwa_icons.py your-logo-512.png

# Or generate placeholders
python ../../../generate_pwa_icons.py
```

### Option 2: Online Tools

1. **RealFaviconGenerator**: https://realfavicongenerator.net/
   - Upload 512x512 PNG
   - Select "Progressive Web App"
   - Download and extract to this folder

2. **PWA Asset Generator**:
   ```bash
   npx pwa-asset-generator logo.png ./
   ```

### Option 3: Manual Creation

1. Create a 512x512 PNG with your logo/branding
2. Use image editor (Photoshop, GIMP, etc.)
3. Resize to each required size
4. Save with exact filenames listed above
5. Optimize with TinyPNG or similar

## Design Guidelines

### Logo Requirements:
- **Format:** PNG with transparency
- **Size:** Square (1:1 aspect ratio)
- **Resolution:** At least 512x512px
- **Colors:** Should work on colored backgrounds
- **Safe Area:** Keep important elements in center 80%

### Android:
- Maskable icons should have 20% padding
- Solid background color (no transparency)
- Use brand colors

### iOS:
- No transparency (use solid background)
- Rounded corners applied by system
- Design within safe area

### Desktop:
- Can use transparency
- Should be recognizable at small sizes
- High contrast recommended

## Testing Icons

After generating icons:

1. **Validate Manifest:**
   ```bash
   python ../../../generate_pwa_icons.py
   # Run verification at the end
   ```

2. **Test in Browser:**
   - Chrome DevTools → Application → Manifest
   - Check all icons load correctly
   - No 404 errors

3. **Test Installation:**
   - Install app on Android
   - Check home screen icon quality
   - Verify splash screen looks good

## Current Status

⚠️ **Icons Not Yet Generated**

The manifest.json currently references these files, but they don't exist yet.

**To Fix:**
1. Run `python ../../../generate_pwa_icons.py your-logo.png`
2. Or manually create all required sizes
3. Place files in this directory

## Icon Checklist

Required icons:
- [ ] icon-72x72.png
- [ ] icon-96x96.png
- [ ] icon-128x128.png
- [ ] icon-144x144.png
- [ ] icon-152x152.png
- [ ] icon-192x192.png
- [ ] icon-384x384.png
- [ ] icon-512x512.png

Additional assets:
- [ ] badge-72x72.png
- [ ] dashboard-96x96.png
- [ ] invoice-96x96.png
- [ ] open-24x24.png
- [ ] close-24x24.png

Other:
- [ ] favicon.ico (in /static/)
- [ ] Screenshots for app stores (optional)

## Temporary Workaround

Until you generate proper icons, you can:

1. **Use a Simple SVG Icon:**
   Create a basic SVG and convert to PNG sizes

2. **Use Text-Based Icons:**
   Generate icons with just "E" letter on colored background

3. **Use Default Browser Icon:**
   App will still work, just won't look as polished

4. **Copy Existing Icons:**
   If you have existing branding, resize those files

## Need Help?

See `/MOBILE_OPTIMIZATION_GUIDE.md` → "Icon Generation" section for detailed instructions.

---

**Last Updated:** February 6, 2026  
**Status:** ⚠️ Pending icon generation
