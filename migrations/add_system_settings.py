"""
Migration: Add system_settings table for managing landing page and app settings
"""

def upgrade(db):
    """Create system_settings table"""
    
    # Create system_settings table
    db.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT DEFAULT 'text',
            category TEXT DEFAULT 'general',
            description TEXT,
            is_public INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Insert default settings
    default_settings = [
        # Contact Information
        ('contact_email', 'support@efrisintegration.nafacademy.com', 'email', 'contact', 'Support email address', 1),
        ('contact_phone', '+256 700 000 000', 'text', 'contact', 'Primary phone number', 1),
        ('contact_whatsapp', '+256700000000', 'text', 'contact', 'WhatsApp number (no spaces or +)', 1),
        ('contact_address', 'Kampala, Uganda', 'text', 'contact', 'Physical address', 1),
        ('business_hours', 'Mon-Fri: 8:00 AM - 6:00 PM (EAT)', 'text', 'contact', 'Business operating hours', 1),
        
        # Social Media Links
        ('social_twitter', 'https://twitter.com/youraccount', 'url', 'social', 'Twitter profile URL', 1),
        ('social_facebook', 'https://facebook.com/youraccount', 'url', 'social', 'Facebook page URL', 1),
        ('social_linkedin', 'https://linkedin.com/company/youraccount', 'url', 'social', 'LinkedIn company page URL', 1),
        
        # Company Information
        ('company_name', 'EFRIS Integration Platform', 'text', 'company', 'Company/Platform name', 1),
        ('company_tagline', 'Leading EFRIS integration solution in Uganda', 'text', 'company', 'Company tagline', 1),
        ('company_description', 'Automate your URA tax compliance with seamless integration to QuickBooks, Xero, and any ERP system.', 'textarea', 'company', 'Company description', 1),
        
        # Landing Page Stats
        ('stat_companies', '500+', 'text', 'stats', 'Number of active companies', 1),
        ('stat_invoices', '50K+', 'text', 'stats', 'Number of invoices fiscalized', 1),
        ('stat_uptime', '99.9%', 'text', 'stats', 'Uptime guarantee percentage', 1),
        
        # Feature Flags
        ('enable_registration', '1', 'boolean', 'features', 'Allow new user registration', 0),
        ('enable_api_docs', '1', 'boolean', 'features', 'Show API documentation', 0),
        ('maintenance_mode', '0', 'boolean', 'features', 'Enable maintenance mode', 0),
        ('maintenance_message', 'System under maintenance. We\'ll be back soon!', 'textarea', 'features', 'Maintenance mode message', 0),
        
        # Pricing
        ('trial_days', '2', 'number', 'pricing', 'Number of free trial days', 0),
        ('pricing_model', 'contact', 'text', 'pricing', 'Pricing model (contact/fixed/tiered)', 0),
        
        # Email Configuration (private)
        ('smtp_host', '', 'text', 'email', 'SMTP server host', 0),
        ('smtp_port', '587', 'number', 'email', 'SMTP server port', 0),
        ('smtp_username', '', 'text', 'email', 'SMTP username', 0),
        ('smtp_password', '', 'password', 'email', 'SMTP password', 0),
        
        # System Configuration
        ('max_companies_per_reseller', '5', 'number', 'system', 'Maximum companies per reseller account', 0),
        ('require_email_verification', '0', 'boolean', 'system', 'Require email verification for new accounts', 0),
    ]
    
    for key, value, stype, category, description, is_public in default_settings:
        db.execute("""
            INSERT OR IGNORE INTO system_settings 
            (setting_key, setting_value, setting_type, category, description, is_public)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (key, value, stype, category, description, is_public))
    
    print("✅ System settings table created and initialized with default values")

def downgrade(db):
    """Remove system_settings table"""
    db.execute("DROP TABLE IF EXISTS system_settings")
    print("✅ System settings table removed")

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect('efris_api.db')
    upgrade(conn)
    conn.commit()
    conn.close()
