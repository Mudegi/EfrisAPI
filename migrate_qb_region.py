#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add qb_region field to companies table
"""
import sys
import os
import sqlite3
import psycopg2
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Get database connection with proper cleanup"""
    try:
        # Try SQLite first (for development)
        if os.path.exists('efris.db'):
            conn = sqlite3.connect('efris.db')
            print("[INFO] Connected to SQLite database: efris.db")
            yield conn
            conn.close()
        else:
            # Try PostgreSQL (for production)
            try:
                conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    database=os.getenv('DB_NAME', 'efris_db'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', 'Admin2026!')
                )
                print("[INFO] Connected to PostgreSQL database")
                yield conn
                conn.close()
            except psycopg2.Error as e:
                print(f"[ERROR] PostgreSQL connection failed: {e}")
                # Fallback to SQLite
                conn = sqlite3.connect('efris.db')
                print("[INFO] Fallback to SQLite database: efris.db")
                yield conn
                conn.close()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        raise

def check_column_exists(cursor, table_name, column_name):
    """Check if column exists in table"""
    try:
        # For SQLite - use PRAGMA table_info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        return column_name in columns
    except sqlite3.Error:
        try:
            # For PostgreSQL
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s AND column_name = %s
            """, (table_name, column_name))
            return cursor.fetchone() is not None
        except Exception:
            return False

def add_qb_region_column():
    """Add qb_region column to companies table"""
    print("[MIGRATION] Starting qb_region column migration...")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if column already exists
        if check_column_exists(cursor, 'companies', 'qb_region'):
            print("[INFO] Column 'qb_region' already exists in companies table")
            return
        
        try:
            # Add qb_region column
            cursor.execute("""
                ALTER TABLE companies 
                ADD COLUMN qb_region VARCHAR(10) DEFAULT 'US'
            """)
            
            # Update existing companies to have 'US' as default
            cursor.execute("""
                UPDATE companies 
                SET qb_region = 'US' 
                WHERE qb_region IS NULL
            """)
            
            conn.commit()
            print("[SUCCESS] Added qb_region column to companies table")
            print("[SUCCESS] Set default value 'US' for existing companies")
            
        except Exception as e:
            print(f"[ERROR] Failed to add qb_region column: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    try:
        add_qb_region_column()
        print("[MIGRATION] QB region migration completed successfully!")
    except Exception as e:
        print(f"[MIGRATION] Migration failed: {e}")
        sys.exit(1)