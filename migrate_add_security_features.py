"""
Migration: Add Security Features
- 2FA fields for users (totp_secret, totp_enabled)
- IP whitelisting for companies (allowed_ips)
- API rate limiting fields (api_rate_limit, api_calls_today, api_last_reset)
"""
from sqlalchemy import create_engine, text
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/efris_multitenant")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("[Migration] Adding security enhancement columns...")
            
            # 1. Add 2FA columns to users table
            print("  [1/6] Adding totp_secret to users...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR(255)"))
                conn.commit()
                print("    ✓ totp_secret added")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("    ⚠ totp_secret already exists")
                else:
                    raise
            
            print("  [2/6] Adding totp_enabled to users...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("    ✓ totp_enabled added")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("    ⚠ totp_enabled already exists")
                else:
                    raise
            
            # 2. Add IP whitelisting to companies table
            print("  [3/6] Adding allowed_ips to companies...")
            try:
                conn.execute(text("ALTER TABLE companies ADD COLUMN allowed_ips TEXT"))
                conn.commit()
                print("    ✓ allowed_ips added (JSON array of IPs)")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("    ⚠ allowed_ips already exists")
                else:
                    raise
            
            # 3. Add API rate limiting to companies table
            print("  [4/6] Adding api_rate_limit to companies...")
            try:
                conn.execute(text("ALTER TABLE companies ADD COLUMN api_rate_limit INTEGER DEFAULT 1000"))
                conn.commit()
                print("    ✓ api_rate_limit added (default: 1000 req/day)")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("    ⚠ api_rate_limit already exists")
                else:
                    raise
            
            print("  [5/6] Adding api_calls_today to companies...")
            try:
                conn.execute(text("ALTER TABLE companies ADD COLUMN api_calls_today INTEGER DEFAULT 0"))
                conn.commit()
                print("    ✓ api_calls_today added")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("    ⚠ api_calls_today already exists")
                else:
                    raise
            
            print("  [6/6] Adding api_last_reset to companies...")
            try:
                conn.execute(text("ALTER TABLE companies ADD COLUMN api_last_reset TIMESTAMP WITH TIME ZONE"))
                conn.commit()
                print("    ✓ api_last_reset added")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("    ⚠ api_last_reset already exists")
                else:
                    raise
            
            print("\n[Migration] ✅ Security features migration completed successfully!")
            print("\n📝 Summary:")
            print("   • 2FA: totp_secret, totp_enabled added to users")
            print("   • IP Whitelisting: allowed_ips added to companies")
            print("   • Rate Limiting: api_rate_limit, api_calls_today, api_last_reset added to companies")
            
        except Exception as e:
            print(f"\n[Migration] ❌ Error: {e}")
            conn.rollback()
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
