"""
Migration: Add System Settings Table for PostgreSQL
Creates system_settings table for configurable landing page and app settings
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    # Connect to PostgreSQL database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/efris_multitenant")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create system_settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id SERIAL PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type VARCHAR(20) DEFAULT 'text',
                category VARCHAR(50) DEFAULT 'general',
                description TEXT,
                is_public INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_settings_key ON system_settings(setting_key)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_settings_category ON system_settings(category)
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
            ('company_name', 'EFRIS Integration Platform', 'text', 'company', 'Company name', 1),
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
            ('max_companies_per_reseller', '5', 'number', 'system', 'Maximum companies per reseller', 0),
            ('require_email_verification', '0', 'boolean', 'system', 'Require email verification for new users', 0),
        ]
        
        for setting in default_settings:
            cursor.execute("""
                INSERT INTO system_settings (setting_key, setting_value, setting_type, category, description, is_public)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (setting_key) DO NOTHING
            """, setting)
        
        # Commit changes
        conn.commit()
        
        print("✅ System settings table created and initialized with default values")
        
        # Show counts
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM system_settings WHERE is_public = 1")
        public = cursor.fetchone()[0]
        
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
