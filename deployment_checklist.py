#!/usr/bin/env python3
"""
Deployment Checklist Script
Run this before pushing to production

Usage:
    python deployment_checklist.py

This checks for common issues before deployment.
"""

import os
import subprocess
import sys

def check(description):
    """Decorator for checks"""
    def decorator(func):
        def wrapper():
            print(f"\n{'='*60}")
            print(f"Checking: {description}")
            print('='*60)
            try:
                result = func()
                if result:
                    print("✅ PASS")
                    return True
                else:
                    print("❌ FAIL")
                    return False
            except Exception as e:
                print(f"❌ ERROR: {e}")
                return False
        return wrapper
    return decorator

@check("requirements.txt exists and has production dependencies")
def check_requirements():
    if not os.path.exists('requirements.txt'):
        print("requirements.txt not found!")
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
        
    # Check for essential packages
    required = ['fastapi', 'uvicorn', 'sqlalchemy', 'requests', 'cryptography']
    missing = [pkg for pkg in required if pkg not in content.lower()]
    
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        return False
    
    print(f"Found all required packages")
    return True

@check(".env file NOT committed to git")
def check_env_not_committed():
    # Check if .env exists and is gitignored
    if os.path.exists('.env'):
        result = subprocess.run(
            ['git', 'check-ignore', '.env'],
            capture_output=True
        )
        if result.returncode == 0:
            print(".env is properly gitignored")
            return True
        else:
            print("⚠️  WARNING: .env exists but not gitignored!")
            return False
    else:
        print(".env not found (will need to create on server)")
        return True

@check("No certificate files committed")
def check_certificates():
    # Check for certificate files
    cert_extensions = ['.p12', '.pfx', '.pem', '.key']
    found = []
    
    for root, dirs, files in os.walk('.'):
        # Skip .git directory
        if '.git' in root:
            continue
        for file in files:
            if any(file.endswith(ext) for ext in cert_extensions):
                found.append(os.path.join(root, file))
    
    if found:
        print(f"⚠️  Certificate files found: {', '.join(found)}")
        print("Make sure these are in .gitignore!")
        return False
    
    print("No certificate files in repository")
    return True

@check("No test dependencies in requirements.txt")
def check_no_test_deps():
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    test_packages = ['pytest', 'locust', 'faker', 'black', 'flake8']
    found = [pkg for pkg in test_packages if pkg in content]
    
    if found:
        print(f"⚠️  Test packages in requirements.txt: {', '.join(found)}")
        print("Move these to requirements-dev.txt")
        return False
    
    print("requirements.txt contains only production packages")
    return True

@check("Database migrations defined (if needed)")
def check_migrations():
    if os.path.exists('run_migrations.py'):
        print("Migration runner exists")
        return True
    else:
        print("⚠️  No migration runner found (create if you have schema changes)")
        return True  # Not critical

@check("GitHub secrets configured")
def check_github_secrets():
    print("⚠️  Manual check required:")
    print("   Go to: GitHub → Repository → Settings → Secrets")
    print("   Required secrets:")
    print("   - SSH_PASSWORD (for Namecheap deployment)")
    print("")
    response = input("Are GitHub secrets configured? (y/n): ").strip().lower()
    return response == 'y'

def summary():
    """Print deployment summary"""
    print("\n" + "="*60)
    print("📋 DEPLOYMENT CHECKLIST COMPLETE")
    print("="*60)
    print("\n🔄 Auto-Deployed on Push:")
    print("   ✅ Code files (.py)")
    print("   ✅ Static files (HTML, CSS, JS)")
    print("   ✅ Dependencies (requirements.txt)")
    print("   ✅ Database migrations (run_migrations.py)")
    print("")
    print("⚠️  Manual Steps Needed If:")
    print("   📝 New .env variables → SSH and edit .env")
    print("   🔐 New certificates → Upload via SFTP")
    print("   🗄️  Complex migrations → SSH and verify")
    print("")
    print("🚀 Ready to deploy?")
    print("   git add .")
    print("   git commit -m 'Your message'")
    print("   git push origin main")
    print("="*60)

def main():
    print("="*60)
    print("🚀 PRE-DEPLOYMENT CHECKLIST")
    print("="*60)
    
    checks = [
        check_requirements,
        check_env_not_committed,
        check_certificates,
        check_no_test_deps,
        check_migrations,
        check_github_secrets
    ]
    
    results = [check() for check in checks]
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} checks passed")
    print("="*60)
    
    if passed == total:
        print("✅ ALL CHECKS PASSED - Safe to deploy!")
        summary()
        return 0
    else:
        print("❌ Some checks failed - Fix issues before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())
