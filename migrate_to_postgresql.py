"""
PostgreSQL Migration Script
Migrates from SQLite to PostgreSQL for production deployment
"""
import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_to_postgresql():
    """
    Migrate data from SQLite to PostgreSQL
    
    Steps:
    1. Create PostgreSQL database
    2. Create all tables in PostgreSQL
    3. Copy data from SQLite to PostgreSQL
    4. Verify data integrity
    """
    
    # SQLite connection (source)
    sqlite_url = os.getenv("DATABASE_URL", "sqlite:///./efris_multitenant.db")
    if not sqlite_url.startswith("sqlite"):
        print("❌ Error: DATABASE_URL must be SQLite for source database")
        sys.exit(1)
    
    # PostgreSQL connection (destination)
    postgres_url = os.getenv("POSTGRES_URL", "")
    if not postgres_url:
        print("❌ Error: POSTGRES_URL environment variable not set")
        print("\nExample: postgresql://user:password@localhost:5432/efris_db")
        sys.exit(1)
    
    print("🚀 Starting migration from SQLite to PostgreSQL...")
    print(f"   Source: {sqlite_url}")
    print(f"   Destination: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    
    # Create engines
    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)
    
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    try:
        # Step 1: Create tables in PostgreSQL
        print("\n📋 Step 1: Creating tables in PostgreSQL...")
        from database.models import Base
        Base.metadata.create_all(bind=postgres_engine)
        print("   ✅ Tables created")
        
        # Step 2: Get list of tables to migrate
        inspector = inspect(sqlite_engine)
        tables = inspector.get_table_names()
        
        print(f"\n📦 Step 2: Found {len(tables)} tables to migrate")
        
        # Step 3: Migrate data table by table
        for table_name in tables:
            print(f"\n   Migrating table: {table_name}...", end=" ")
            
            # Get data from SQLite
            result = sqlite_session.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            
            if not rows:
                print("(empty)")
                continue
            
            # Get column names
            columns = result.keys()
            
            # Insert into PostgreSQL
            for row in rows:
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                row_dict = dict(zip(columns, row))
                try:
                    postgres_session.execute(text(insert_sql), row_dict)
                except Exception as e:
                    print(f"\n   ⚠️  Error inserting row: {e}")
                    print(f"   Row data: {row_dict}")
            
            postgres_session.commit()
            print(f"✅ ({len(rows)} rows)")
        
        # Step 4: Verify migration
        print("\n🔍 Step 4: Verifying migration...")
        verification_passed = True
        
        for table_name in tables:
            sqlite_count = sqlite_session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            postgres_count = postgres_session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            
            if sqlite_count != postgres_count:
                print(f"   ❌ {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
                verification_passed = False
            else:
                print(f"   ✅ {table_name}: {postgres_count} rows")
        
        if verification_passed:
            print("\n🎉 Migration completed successfully!")
            print("\n📝 Next steps:")
            print("   1. Update .env: DATABASE_URL=" + postgres_url)
            print("   2. Backup SQLite file: cp efris_multitenant.db efris_multitenant.db.backup")
            print("   3. Restart your API: py api_multitenant.py")
            print("   4. Test all endpoints thoroughly")
        else:
            print("\n⚠️  Migration completed with warnings. Review the output above.")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        postgres_session.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        sqlite_session.close()
        postgres_session.close()


def test_postgresql_connection():
    """Test PostgreSQL connection"""
    postgres_url = os.getenv("POSTGRES_URL", "")
    if not postgres_url:
        print("❌ Error: POSTGRES_URL environment variable not set")
        print("\nAdd to .env file:")
        print("POSTGRES_URL=postgresql://user:password@localhost:5432/efris_db")
        sys.exit(1)
    
    try:
        engine = create_engine(postgres_url)
        connection = engine.connect()
        result = connection.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        connection.close()
        
        print("✅ PostgreSQL connection successful!")
        print(f"   Version: {version}")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def create_postgres_database():
    """Helper to create PostgreSQL database"""
    print("\n📚 PostgreSQL Database Setup Guide")
    print("=" * 50)
    print("\n1. Install PostgreSQL:")
    print("   - Ubuntu: sudo apt install postgresql postgresql-contrib")
    print("   - macOS: brew install postgresql")
    print("   - Windows: Download from postgresql.org")
    
    print("\n2. Create database and user:")
    print("   sudo -u postgres psql")
    print("   CREATE DATABASE efris_db;")
    print("   CREATE USER efris_user WITH PASSWORD 'your_password';")
    print("   GRANT ALL PRIVILEGES ON DATABASE efris_db TO efris_user;")
    print("   \\q")
    
    print("\n3. Add to .env file:")
    print("   POSTGRES_URL=postgresql://efris_user:your_password@localhost:5432/efris_db")
    
    print("\n4. Install PostgreSQL driver:")
    print("   pip install psycopg2-binary")
    
    print("\n5. Test connection:")
    print("   py migrate_to_postgresql.py --test")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_postgresql_connection()
        elif sys.argv[1] == "--help":
            create_postgres_database()
        else:
            print("Usage:")
            print("  py migrate_to_postgresql.py          # Run migration")
            print("  py migrate_to_postgresql.py --test   # Test PostgreSQL connection")
            print("  py migrate_to_postgresql.py --help   # Show setup guide")
    else:
        # Run migration
        migrate_to_postgresql()
