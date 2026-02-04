"""
Quick test script to verify SEO endpoints
"""
import requests
import time

print("Testing SEO Endpoints...")
print("=" * 50)

base_url = "http://localhost:8001"

# Wait for server to be ready
time.sleep(2)

# Test 1: robots.txt
print("\n1. Testing /robots.txt")
try:
    response = requests.get(f"{base_url}/robots.txt", timeout=5)
    if response.status_code == 200:
        print("✅ robots.txt endpoint working!")
        print(f"   Content preview: {response.text[:100]}...")
    else:
        print(f"❌ robots.txt returned status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: sitemap.xml
print("\n2. Testing /sitemap.xml")
try:
    response = requests.get(f"{base_url}/sitemap.xml", timeout=5)
    if response.status_code == 200:
        print("✅ sitemap.xml endpoint working!")
        print(f"   Content preview: {response.text[:100]}...")
    else:
        print(f"❌ sitemap.xml returned status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Landing page meta tags
print("\n3. Testing landing page SEO meta tags")
try:
    response = requests.get(f"{base_url}/", timeout=5)
    if response.status_code == 200:
        content = response.text
        
        checks = [
            ('og:title' in content, 'Open Graph title'),
            ('og:description' in content, 'Open Graph description'),
            ('twitter:card' in content, 'Twitter Card'),
            ('application/ld+json' in content, 'Schema.org JSON-LD'),
            ('EFRIS integration Uganda' in content, 'Primary keyword'),
        ]
        
        print("✅ Landing page loaded!")
        for passed, check_name in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")
    else:
        print(f"❌ Landing page returned status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 4: About page
print("\n4. Testing /about page")
try:
    response = requests.get(f"{base_url}/about", timeout=5)
    if response.status_code == 200:
        print("✅ About page working!")
        content = response.text
        if 'AboutPage' in content:
            print("   ✅ AboutPage schema found")
        if 'Our Mission' in content:
            print("   ✅ SEO content loaded")
    else:
        print(f"❌ About page returned status {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("SEO Test Complete!")
