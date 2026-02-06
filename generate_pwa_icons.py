"""
PWA Icon Generator
Generates all required icon sizes for Progressive Web App from a source image.

Usage:
    python generate_pwa_icons.py logo.png

Requirements:
    pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Icon sizes required for PWA
ICON_SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Output directory
OUTPUT_DIR = "static/icons"

def create_placeholder_icon(size, output_path):
    """Create a placeholder icon with EFRIS branding"""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Add simple design
    # Draw circle
    margin = size // 10
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#764ba2', outline='white', width=max(2, size//50))
    
    # Add text
    try:
        # Try to use a nice font, fall back to default
        font_size = size // 4
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    except:
        font = None
    
    text = "E"
    if font:
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        # Estimate size without font
        text_width = size // 3
        text_height = size // 3
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    
    draw.text((text_x, text_y), text, fill='white', font=font)
    
    # Save
    img.save(output_path, 'PNG', optimize=True)
    print(f"✓ Created {os.path.basename(output_path)} ({size}x{size})")

def generate_icons_from_source(source_path):
    """Generate all icon sizes from source image"""
    if not os.path.exists(source_path):
        print(f"✗ Error: Source image '{source_path}' not found")
        return False
    
    try:
        # Open source image
        source = Image.open(source_path)
        
        # Convert to RGBA if needed
        if source.mode != 'RGBA':
            source = source.convert('RGBA')
        
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print(f"Generating icons from {source_path}...")
        print(f"Source size: {source.size[0]}x{source.size[1]}")
        print("")
        
        # Generate each size
        for size in ICON_SIZES:
            output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
            
            # Resize with high-quality resampling
            resized = source.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save with optimization
            resized.save(output_path, 'PNG', optimize=True)
            
            file_size = os.path.getsize(output_path)
            print(f"✓ Created icon-{size}x{size}.png ({file_size // 1024}KB)")
        
        print("")
        print(f"✅ Successfully generated {len(ICON_SIZES)} icons in {OUTPUT_DIR}/")
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def generate_placeholder_icons():
    """Generate placeholder icons with EFRIS branding"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Generating placeholder EFRIS icons...")
    print("")
    
    for size in ICON_SIZES:
        output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
        create_placeholder_icon(size, output_path)
    
    print("")
    print(f"✅ Generated {len(ICON_SIZES)} placeholder icons in {OUTPUT_DIR}/")
    print("")
    print("📋 Next steps:")
    print("1. Replace placeholders with your actual logo:")
    print(f"   python {os.path.basename(__file__)} your-logo.png")
    print("")
    print("2. Or create a high-quality 512x512 PNG logo and run:")
    print(f"   python {os.path.basename(__file__)} logo-512.png")

def generate_additional_assets():
    """Generate additional PWA assets (badges, shortcuts icons)"""
    additional_sizes = {
        'badge-72x72.png': 72,
        'dashboard-96x96.png': 96,
        'invoice-96x96.png': 96,
        'open-24x24.png': 24,
        'close-24x24.png': 24
    }
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Generating additional PWA assets...")
    print("")
    
    for filename, size in additional_sizes.items():
        output_path = os.path.join(OUTPUT_DIR, filename)
        create_placeholder_icon(size, output_path)
    
    print("")
    print("✅ Generated additional assets")

def create_favicon():
    """Create favicon.ico with multiple sizes"""
    try:
        from PIL import Image
        
        # Use the 192x192 icon as source
        source_path = os.path.join(OUTPUT_DIR, "icon-192x192.png")
        
        if os.path.exists(source_path):
            img = Image.open(source_path)
            
            # Create multiple sizes for .ico
            sizes = [(16, 16), (32, 32), (48, 48)]
            favicon_images = []
            
            for size in sizes:
                resized = img.resize(size, Image.Resampling.LANCZOS)
                favicon_images.append(resized)
            
            # Save as .ico
            favicon_path = os.path.join("static", "favicon.ico")
            favicon_images[0].save(
                favicon_path,
                format='ICO',
                sizes=[img.size for img in favicon_images],
                append_images=favicon_images[1:]
            )
            
            print(f"✓ Created favicon.ico with {len(sizes)} sizes")
            return True
    except Exception as e:
        print(f"⚠ Could not create favicon.ico: {str(e)}")
        return False

def verify_manifest():
    """Verify manifest.json references correct icon files"""
    manifest_path = "static/manifest.json"
    
    if not os.path.exists(manifest_path):
        print(f"⚠ Warning: {manifest_path} not found")
        return False
    
    print("")
    print("📋 Verifying manifest.json...")
    
    import json
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        icons = manifest.get('icons', [])
        missing = []
        
        for icon in icons:
            icon_path = icon['src'].replace('/static/', 'static/')
            if not os.path.exists(icon_path):
                missing.append(icon_path)
        
        if missing:
            print("⚠ Missing icon files:")
            for path in missing:
                print(f"  - {path}")
            return False
        else:
            print(f"✓ All {len(icons)} icons referenced in manifest exist")
            return True
            
    except Exception as e:
        print(f"✗ Error reading manifest: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("📱 EFRIS PWA Icon Generator")
    print("=" * 60)
    print("")
    
    if len(sys.argv) > 1:
        # Generate from source image
        source_path = sys.argv[1]
        success = generate_icons_from_source(source_path)
        
        if success:
            generate_additional_assets()
            create_favicon()
            verify_manifest()
    else:
        # Generate placeholders
        print("No source image provided. Generating placeholders...")
        print("")
        generate_placeholder_icons()
        generate_additional_assets()
        create_favicon()
    
    print("")
    print("=" * 60)
    print("✨ Icon generation complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
