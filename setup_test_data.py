#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test to setup initial data and test QB region functionality
"""
import os
import sqlite3
from datetime import datetime

# Set SQLite as database
os.environ['DATABASE_URL'] = 'sqlite:///efris.db'

def setup_test_data():
    """Create test company and user data"""
    conn = sqlite3.connect('efris.db')
    cursor = conn.cursor()
    
    try:
        # Check what columns exist in users table
        cursor.execute("PRAGMA table_info(users)")
        users_columns = [row[1] for row in cursor.fetchall()]
        print(f"Users table columns: {users_columns}")
        
        # Check what columns exist in company_users table  
        cursor.execute("PRAGMA table_info(company_users)")
        company_users_columns = [row[1] for row in cursor.fetchall()]
        print(f"Company_users table columns: {company_users_columns}")
        
        # Create test user (adapt to actual columns)
        cursor.execute('''
            INSERT OR IGNORE INTO users (email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES ('admin@wandera.com', '$2b$12$hashed_password_here', 'Admin User', 1, ?, ?)
        ''', (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        # Create test company
        cursor.execute('''
            INSERT OR IGNORE INTO companies 
            (name, tin, device_no, qb_region, is_active, created_at, updated_at)
            VALUES ('Wandera Ltd', '1014409555', '1014409555_02', 'US', 1, ?, ?)
        ''', (datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        
        # Get company and user IDs
        cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@wandera.com',))
        user_result = cursor.fetchone()
        user_id = user_result[0] if user_result else None
        
        cursor.execute('SELECT id FROM companies WHERE tin = ?', ('1014409555',))
        company_result = cursor.fetchone()
        company_id = company_result[0] if company_result else None
        
        # Link user to company (adapt to actual columns)
        if user_id and company_id:
            cursor.execute('''
                INSERT OR IGNORE INTO company_users (user_id, company_id, role)
                VALUES (?, ?, 'admin')
            ''', (user_id, company_id))
        
        conn.commit()
        
        print(f"✅ Test data created successfully!")
        print(f"   User ID: {user_id}")
        print(f"   Company ID: {company_id}")
        
        # Verify QB region
        cursor.execute('SELECT name, qb_region FROM companies WHERE id = ?', (company_id,))
        result = cursor.fetchone()
        if result:
            print(f"   Company: {result[0]}")
            print(f"   QB Region: {result[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    setup_test_data()