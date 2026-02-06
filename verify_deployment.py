"""
Pre-Deployment Verification Script
Tests all critical components before production deployment
"""
import sys
import os
import importlib
import subprocess
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_info(message):
    print(f"{BLUE}ℹ️  {message}{RESET}")

def print_section(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  {title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

errors = []
warnings = []

# ============================================================================
# 1. CHECK PYTHON VERSION
# ============================================================================
print_section("1. Checking Python Version")
python_version = sys.version_info
if python_version.major == 3 and python_version.minor >= 8:
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro}")
else:
    print_error(f"Python 3.8+ required, found {python_version.major}.{python_version.minor}")
    errors.append("Python version")

# ============================================================================
# 2. CHECK REQUIRED FILES
# ============================================================================
print_section("2. Checking Required Files")
required_files = [
    'api_multitenant.py',
    'database/models.py',
    'database/connection.py',
    'efris_client.py',
    'auth.py',
    'security_utils.py',
    '.env',
    'static/landing.html',
    'static/owner_portal.html',
    'EFRIS_API_Postman_Collection.json'
]

for file in required_files:
    if os.path.exists(file):
        print_success(f"Found: {file}")
    else:
        print_error(f"Missing: {file}")
        errors.append(f"Missing file: {file}")

# ============================================================================
# 3. CHECK DEPENDENCIES
# ============================================================================
print_section("3. Checking Python Dependencies")
required_packages = [
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('sqlalchemy', 'sqlalchemy'),
    ('psycopg2', 'psycopg2'),
    ('pydantic', 'pydantic'),
    ('python-jose', 'jose'),
    ('passlib', 'passlib'),
    ('python-dotenv', 'dotenv'),
    ('requests', 'requests'),
    ('cryptography', 'cryptography'),
    ('pyotp', 'pyotp')
]

for package_name, import_name in required_packages:
    try:
        importlib.import_module(import_name)
        print_success(f"Installed: {package_name}")
    except ImportError:
        print_error(f"Missing package: {package_name}")
        errors.append(f"Missing package: {package_name}")

# ============================================================================
# 4. CHECK ENVIRONMENT VARIABLES
# ============================================================================
print_section("4. Checking Environment Variables")
from dotenv import load_dotenv
load_dotenv()

env_vars = {
    'DATABASE_URL': 'Database connection string',
    'SECRET_KEY': 'JWT secret key',
    'EFRIS_BASE_URL_TEST': 'EFRIS test environment URL',
    'EFRIS_BASE_URL_PROD': 'EFRIS production environment URL'
}

for var, description in env_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'SECRET' in var or 'PASSWORD' in var:
            display_value = value[:8] + '...' if len(value) > 8 else '***'
        else:
            display_value = value[:50] + '...' if len(value) > 50 else value
        print_success(f"{var}: {display_value}")
    else:
        print_warning(f"{var} not set ({description})")
        warnings.append(f"Missing env var: {var}")

# ============================================================================
# 5. TEST DATABASE CONNECTION
# ============================================================================
print_section("5. Testing Database Connection")
try:
    import psycopg2
    DATABASE_URL = os.getenv('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Check if tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    
    required_tables = ['users', 'companies', 'company_users', 'invoices', 'products', 'system_settings']
    found_tables = [t[0] for t in tables]
    
    for table in required_tables:
        if table in found_tables:
            print_success(f"Table exists: {table}")
        else:
            print_error(f"Missing table: {table}")
            errors.append(f"Missing table: {table}")
    
    cursor.close()
    conn.close()
    print_success("Database connection successful")
    
except Exception as e:
    print_error(f"Database connection failed: {e}")
    errors.append("Database connection")

# ============================================================================
# 6. SYNTAX CHECK - MAIN FILES
# ============================================================================
print_section("6. Checking Python Syntax")
python_files = [
    'api_multitenant.py',
    'database/models.py',
    'database/connection.py',
    'efris_client.py',
    'auth.py',
    'security_utils.py'
]

for file in python_files:
    if os.path.exists(file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                compile(f.read(), file, 'exec')
            print_success(f"Syntax OK: {file}")
        except SyntaxError as e:
            print_error(f"Syntax error in {file}: {e}")
            errors.append(f"Syntax error: {file}")
    else:
        print_warning(f"File not found: {file}")

# ============================================================================
# 7. TEST IMPORTS
# ============================================================================
print_section("7. Testing Module Imports")
try:
    sys.path.insert(0, os.getcwd())
    
    # Test database imports
    from database.connection import get_db, init_db
    print_success("Import: database.connection")
    
    from database.models import User, Company, SystemSettings
    print_success("Import: database.models")
    
    # Test EFRIS client
    from efris_client import EfrisManager
    print_success("Import: efris_client")
    
    # Test auth
    from auth import get_current_user
    print_success("Import: auth")
    
    # Test security utils
    from security_utils import generate_totp_secret
    print_success("Import: security_utils")
    
except Exception as e:
    print_error(f"Import failed: {e}")
    errors.append("Module imports")

# ============================================================================
# 8. CHECK STATIC FILES
# ============================================================================
print_section("8. Checking Static Files")
static_files = {
    'static/landing.html': ['UG EFRIS INTEGRATION PLATFORM', 'Unlimited Companies per Account'],
    'static/owner_portal.html': ['Settings', 'owner-dashboard']
}

for file, keywords in static_files.items():
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            found_keywords = [kw for kw in keywords if kw in content]
            if len(found_keywords) == len(keywords):
                print_success(f"{file} - All keywords found")
            else:
                missing = set(keywords) - set(found_keywords)
                print_warning(f"{file} - Missing keywords: {missing}")
    else:
        print_error(f"Missing: {file}")
        errors.append(f"Missing file: {file}")

# ============================================================================
# 9. CHECK MIGRATIONS
# ============================================================================
print_section("9. Checking Migrations")
if os.path.exists('migrations'):
    migration_files = list(Path('migrations').glob('*.py'))
    print_info(f"Found {len(migration_files)} migration files")
    for mig in migration_files[:5]:  # Show first 5
        print_success(f"  {mig.name}")
else:
    print_warning("No migrations folder found")
    warnings.append("No migrations folder")

# ============================================================================
# 10. CHECK API ENDPOINTS (Quick Validation)
# ============================================================================
print_section("10. Validating API Endpoint Definitions")
try:
    with open('api_multitenant.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    endpoints = [
        '@app.post("/api/auth/register")',
        '@app.post("/api/auth/login")',
        '@app.get("/api/settings/public")',
        '@app.post("/api/companies")',
        '@app.post("/api/external/efris/submit-invoice")',
        '@app.get("/api/external/efris/excise-duty")',
        '@app.post("/api/external/efris/stock-decrease")'
    ]
    
    for endpoint in endpoints:
        if endpoint in content:
            print_success(f"Found: {endpoint}")
        else:
            print_warning(f"Not found: {endpoint}")
            warnings.append(f"Endpoint missing: {endpoint}")
            
except Exception as e:
    print_error(f"Could not validate endpoints: {e}")

# ============================================================================
# 11. CHECK SECURITY SETTINGS
# ============================================================================
print_section("11. Checking Security Settings")
try:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if SECRET_KEY and SECRET_KEY != 'your-secret-key-change-in-production':
        print_success("SECRET_KEY is customized (not default)")
    else:
        print_error("SECRET_KEY is default value - CHANGE FOR PRODUCTION!")
        errors.append("Default SECRET_KEY")
    
    # Check CORS settings
    with open('api_multitenant.py', 'r', encoding='utf-8') as f:
        if 'CORSMiddleware' in f.read():
            print_success("CORS middleware configured")
        else:
            print_warning("CORS middleware not found")
            
except Exception as e:
    print_warning(f"Could not check security: {e}")

# ============================================================================
# 12. SUMMARY
# ============================================================================
print_section("DEPLOYMENT VERIFICATION SUMMARY")

if errors:
    print(f"\n{RED}{'='*60}{RESET}")
    print(f"{RED}❌ VERIFICATION FAILED - {len(errors)} ERROR(S){RESET}")
    print(f"{RED}{'='*60}{RESET}\n")
    print(f"{RED}Critical Issues:{RESET}")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")
    print(f"\n{RED}⚠️  DO NOT DEPLOY TO PRODUCTION{RESET}")
    print(f"{RED}Fix these issues first, then run verification again.{RESET}\n")
    sys.exit(1)
    
elif warnings:
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}⚠️  VERIFICATION PASSED WITH WARNINGS - {len(warnings)} WARNING(S){RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")
    print(f"{YELLOW}Non-Critical Issues:{RESET}")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")
    print(f"\n{YELLOW}Review warnings before deploying to production.{RESET}")
    print(f"{GREEN}You may proceed with caution.{RESET}\n")
    sys.exit(0)
    
else:
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}✅ ALL CHECKS PASSED!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")
    print(f"{GREEN}🚀 System is ready for production deployment!{RESET}\n")
    print(f"{BLUE}Next steps:{RESET}")
    print(f"  1. Commit your changes to git")
    print(f"  2. Push to your production server")
    print(f"  3. Restart the API server")
    print(f"  4. Monitor logs for any issues")
    print(f"\n{GREEN}Good luck! 🎉{RESET}\n")
    sys.exit(0)
