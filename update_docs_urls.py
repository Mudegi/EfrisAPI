"""
Script to update documentation URLs from localhost to production domain
"""
import os
import re

# Production domain
PRODUCTION_DOMAIN = "https://efrisintegration.nafacademy.com"

# Files to update
DEVELOPER_PACKAGE_DIR = "DEVELOPER_PACKAGE"

# URL patterns to replace
replacements = [
    ("http://127.0.0.1:8001", PRODUCTION_DOMAIN),
    ("http://localhost:8001", PRODUCTION_DOMAIN),
    ("https://yourdomain.com", PRODUCTION_DOMAIN),
]

def update_file(filepath):
    """Update URLs in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for old_url, new_url in replacements:
        content = content.replace(old_url, new_url)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Update all documentation files"""
    updated_files = []
    
    # Get all .md files in DEVELOPER_PACKAGE directory
    for root, dirs, files in os.walk(DEVELOPER_PACKAGE_DIR):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                if update_file(filepath):
                    updated_files.append(filepath)
                    print(f"✓ Updated: {filepath}")
    
    if updated_files:
        print(f"\n✅ Successfully updated {len(updated_files)} files")
        print(f"   Production URL: {PRODUCTION_DOMAIN}")
    else:
        print("No files needed updating")

if __name__ == "__main__":
    main()
