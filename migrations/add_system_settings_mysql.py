"""
Migration: Add System Settings Table for MySQL
Creates system_settings table for configurable landing page and app settings
"""
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    # Get MySQL connection string from .env
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    
    # Parse MySQL connection string: mysql+pymysql://user:pass@host/dbname
    if "mysql+pymysql://" in DATABASE_URL:
        # Remove mysql+pymysql:// prefix
        connection_string = DATABASE_URL.replace("mysql+pymysql://", "")
        
        # Split into parts
        if "@" in connection_string:
            user_pass, host_db = connection_string.split("@")
            username, password = user_pass.split(":")
            
            if "/" in host_db:
                host, database = host_db.split("/")
            else:
                host = host_db
                database = "nafazplp_efris_prod"
        else:
            raise ValueError("Invalid DATABASE_URL format")
    else:
        raise ValueError("DATABASE_URL must be MySQL format: mysql+pymysql://user:pass@host/dbname")
    
    try:
        # Connect to MySQL database
        conn = pymysql.connect(
            host=host,
            user=username,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        # Create system_settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type VARCHAR(20) DEFAULT 'text',
                category VARCHAR(50) DEFAULT 'general',
                description TEXT,
                is_public INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_settings_key (setting_key),
                INDEX idx_settings_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # Insert default settings
        default_settings = [
            # Contact Information (Public)
            ('contact_email', 'support@efrisintegration.nafacademy.com', 'email', 'contact', 'Support email address', 1),
            ('contact_phone', '+256 700 000 000', 'text', 'contact', 'Primary phone number', 1),
            ('contact_whatsapp', '+256700000000', 'text', 'contact', 'WhatsApp contact number', 1),
            ('contact_address', 'Kampala, Uganda', 'text', 'contact', 'Physical business address', 1),
            ('business_hours', 'Mon-Fri: 8:00 AM - 6:00 PM (EAT)', 'text', 'contact', 'Business operating hours', 1),
            
            # Social Media (Public)
            ('social_twitter', 'https://twitter.com/efrisug', 'url', 'social', 'Twitter profile URL', 1),
            ('social_facebook', 'https://facebook.com/efrisuganda', 'url', 'social', 'Facebook page URL', 1),
            ('social_linkedin', 'https://linkedin.com/company/efris', 'url', 'social', 'LinkedIn company page URL', 1),
            
            # Company Information (Public)
            ('company_name', 'UG EFRIS INTEGRATION PLATFORM', 'text', 'company', 'Company name', 1),
            ('company_tagline', 'Your trusted EFRIS integration solution', 'text', 'company', 'Company tagline/slogan', 1),
            ('company_description', 'Leading EFRIS integration platform helping businesses comply with Uganda Revenue Authority e-invoicing requirements', 'textarea', 'company', 'Company description', 1),
            
            # Landing Page Stats (Public)
            ('stat_companies', '500+', 'text', 'stats', 'Number of active companies', 1),
            ('stat_invoices', '50K+', 'text', 'stats', 'Total invoices fiscalized', 1),
            ('stat_uptime', '99.9%', 'text', 'stats', 'System uptime percentage', 1),
            
            # Feature Flags (Private)
            ('enable_registration', '1', 'boolean', 'features', 'Allow new user registrations', 0),
            ('enable_api_docs', '1', 'boolean', 'features', 'Show API documentation publicly', 0),
            ('maintenance_mode', '0', 'boolean', 'features', 'Enable maintenance mode', 0),
            ('maintenance_message', 'System maintenance in progress. Please check back soon.', 'textarea', 'features', 'Maintenance mode message', 0),
            
            # Pricing (Public)
            ('trial_days', '2', 'number', 'pricing', 'Free trial period in days', 1),
            ('pricing_model', 'contact', 'text', 'pricing', 'Pricing model: contact/fixed/tiered', 1),
            
            # Email Configuration (Private)
            ('smtp_host', '', 'text', 'email', 'SMTP server host', 0),
            ('smtp_port', '587', 'number', 'email', 'SMTP server port', 0),
            ('smtp_username', '', 'email', 'email', 'SMTP username', 0),
            ('smtp_password', '', 'password', 'email', 'SMTP password', 0),
            
            # System Configuration (Private)
            ('max_companies_per_reseller', '9999', 'number', 'system', 'Maximum companies per reseller (unlimited)', 0),
            ('require_email_verification', '0', 'boolean', 'system', 'Require email verification for new users', 0),
        ]
        
        for setting in default_settings:
            cursor.execute("""
                INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description, is_public)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE setting_key=setting_key
            """, setting)
        
        # Commit changes
        conn.commit()
        
        print("✅ System settings table created and initialized with default values")
        
        # Show counts
        cursor.execute("SELECT COUNT(*) as total FROM system_settings")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as public FROM system_settings WHERE is_public = 1")
        public = cursor.fetchone()['public']
        
        print(f"   📊 Total settings: {total}")
        print(f"   🌐 Public settings: {public}")
        print(f"   🔒 Private settings: {total - public}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
