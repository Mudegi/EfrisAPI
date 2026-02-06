#!/usr/bin/env python3
"""
Database Migration Runner
Automatically runs when deploying via GitHub Actions

This ensures database schema stays up to date with code changes.
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.getenv('DATABASE_PATH', 'efris_api.db')

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_migrations():
    """Run all database migrations"""
    log("Starting database migrations...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create migrations tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get applied migrations
        cursor.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cursor.fetchall()}
        
        # Define migrations (add new ones here)
        migrations = [
            # Example:
            # (1, "initial_schema", """
            #     CREATE TABLE IF NOT EXISTS users (
            #         id INTEGER PRIMARY KEY AUTOINCREMENT,
            #         email TEXT UNIQUE NOT NULL
            #     )
            # """),
        ]
        
        # Run pending migrations
        for version, name, sql in migrations:
            if version not in applied:
                log(f"Applying migration {version}: {name}")
                cursor.executescript(sql)
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                    (version, name)
                )
                conn.commit()
                log(f"✅ Migration {version} applied successfully")
            else:
                log(f"⏭️  Migration {version} already applied, skipping")
        
        conn.close()
        log("✅ All migrations completed successfully")
        return True
        
    except Exception as e:
        log(f"❌ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    exit(0 if success else 1)
