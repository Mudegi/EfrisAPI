"""
Quick setup script for EFRIS SaaS Platform
Runs all necessary steps to get the platform ready
"""
import os
import secrets
import subprocess
import sys

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def check_requirements():
    """Check if all required packages are installed"""
    print_header("STEP 1: Checking Dependencies")
    
    missing = []
    required = ['fastapi', 'uvicorn', 'sqlalchemy', 'passlib', 'jose', 'python-multipart']
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} - MISSING")
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
        print("✓ All packages installed!")
    else:
        print("\n✓ All dependencies satisfied!")
    
    return True

def setup_env():
    """Create .env file from template if it doesn't exist"""
    print_header("STEP 2: Environment Configuration")
    
    if os.path.exists('.env'):
        print("✓ .env file already exists")
        return True
    
    if not os.path.exists('.env.example'):
        print("✗ .env.example not found")
        return False
    
    # Generate a secure JWT secret
    jwt_secret = secrets.token_urlsafe(32)
    
    print("Creating .env from template...")
    with open('.env.example', 'r') as example:
        content = example.read()
    
    # Replace placeholder with actual secret
    content = content.replace(
        'your-super-secret-key-min-32-chars-long-CHANGE-THIS-IN-PRODUCTION',
        jwt_secret
    )
    
    with open('.env', 'w') as env_file:
        env_file.write(content)
    
    print(f"✓ Created .env file with secure JWT secret")
    print(f"  JWT Secret: {jwt_secret[:20]}... (auto-generated)")
    
    return True

def run_migration():
    """Run database migration"""
    print_header("STEP 3: Database Migration")
    
    if not os.path.exists('migrate_to_saas.py'):
        print("✗ migrate_to_saas.py not found")
        return False
    
    print("Running migration script...")
    try:
        # Run as subprocess instead of exec to avoid encoding issues
        result = subprocess.run(
            [sys.executable, 'migrate_to_saas.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Migration completed successfully!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"✗ Migration failed:")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            return False
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

def print_success():
    """Print success message with next steps"""
    print_header("🎉 SETUP COMPLETE!")
    
    print("""
Your EFRIS SaaS Platform is ready to use!

DEFAULT ADMIN LOGIN:
  Email:    admin@efris.local
  Password: admin123
  
  ⚠ IMPORTANT: Change this password after first login!

NEXT STEPS:
  1. Start the server:
     py api_multitenant.py
  
  2. Open your browser:
     http://localhost:8001
  
  3. Register your first user account or login as admin
  
  4. Create a company and start using the API!

NEED HELP?
  📖 Read: SAAS_SETUP_GUIDE.md
  📖 Read: TRANSFORMATION_SUMMARY.md
  📖 Read: DEPLOYMENT_CHECKLIST.md

PRODUCTION DEPLOYMENT:
  - Set APP_ENV=production in .env
  - Change JWT_SECRET_KEY in .env
  - Use PostgreSQL instead of SQLite
  - Follow DEPLOYMENT_CHECKLIST.md

Happy fiscalizing! 🚀
""")

def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           EFRIS SaaS Platform - Quick Setup Wizard                ║
║                                                                   ║
║  This script will:                                                ║
║    1. Install required Python packages                            ║
║    2. Create .env configuration file                              ║
║    3. Run database migration                                      ║
║    4. Create default admin user                                   ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    try:
        # Run setup steps
        if not check_requirements():
            print("\n✗ Failed to install dependencies")
            return False
        
        if not setup_env():
            print("\n✗ Failed to setup environment")
            return False
        
        if not run_migration():
            print("\n✗ Failed to run migration")
            return False
        
        # Success!
        print_success()
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠ Setup cancelled by user")
        return False
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
