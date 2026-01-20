#!/usr/bin/env python3
"""
Create a proper test user with correct password hash
"""
import os
import sqlite3
from datetime import datetime

# Set SQLite as database
os.environ['DATABASE_URL'] = 'sqlite:///efris.db'

from auth.security import get_password_hash

def create_proper_user():
    """Create user with proper bcrypt hash"""
    # Generate proper password hash
    password = "Admin2026!"
    hashed_password = get_password_hash(password)
    
    print(f"Creating user with password: {password}")
    print(f"Generated hash: {hashed_password}")
    
    conn = sqlite3.connect('efris.db')
    cursor = conn.cursor()
    
    try:
        # Create test user with proper hash
        cursor.execute('''
            INSERT INTO users (email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'admin@wandera.com', 
            hashed_password, 
            'Admin User', 
            1, 
            datetime.utcnow().isoformat(), 
            datetime.utcnow().isoformat()
        ))
        
        # Get user ID
        user_id = cursor.lastrowid
        
        # Get company ID
        cursor.execute('SELECT id FROM companies WHERE tin = ?', ('1014409555',))
        company_result = cursor.fetchone()
        company_id = company_result[0] if company_result else None
        
        # Link user to company
        if company_id:
            cursor.execute('''
                INSERT OR IGNORE INTO company_users (user_id, company_id, role)
                VALUES (?, ?, ?)
            ''', (user_id, company_id, 'admin'))
        
        conn.commit()
        print(f"✅ User created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Company ID: {company_id}")
        print(f"   Email: admin@wandera.com")
        print(f"   Password: {password}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    create_proper_user()