"""
Email Notification Service
Sends transactional emails for user registration, payments, and system events
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """Handle email notifications"""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
        self.from_name = os.getenv("FROM_NAME", "EFRIS Platform")
        self.enabled = bool(self.smtp_user and self.smtp_password)
        
        if not self.enabled:
            print("⚠️  Email service not configured. Add SMTP credentials to .env")
    
    def send_email(self, to_email: str, subject: str, html_body: str, 
                   text_body: Optional[str] = None) -> bool:
        """
        Send email
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)
        
        Returns:
            Boolean indicating success
        """
        if not self.enabled:
            print(f"📧 Email not sent (service disabled): {subject} to {to_email}")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Email sent: {subject} to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def send_welcome_email(self, to_email: str, full_name: str, role: str = "client"):
        """Send welcome email after registration"""
        subject = "Welcome to EFRIS Platform!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to EFRIS Platform!</h1>
                </div>
                <div class="content">
                    <p>Hi {full_name},</p>
                    
                    <p>Your account has been created successfully! You now have access to our 
                    comprehensive EFRIS integration platform.</p>
                    
                    <h3>What's Next?</h3>
                    <ol>
                        <li><strong>Login:</strong> Visit <a href="http://localhost:8001">http://localhost:8001</a></li>
                        <li><strong>Connect ERP:</strong> Link your QuickBooks, Xero, or Zoho account</li>
                        <li><strong>Fiscalize:</strong> Start processing invoices automatically</li>
                    </ol>
                    
                    <p style="background: #fff3cd; padding: 15px; border-radius: 5px;">
                        ⏰ <strong>Trial Period:</strong> You have a 2-day free trial to explore all features.
                    </p>
                    
                    <center>
                        <a href="http://localhost:8001/dashboard" class="button">Go to Dashboard</a>
                    </center>
                    
                    <p>If you have any questions, reply to this email and we'll be happy to help!</p>
                    
                    <p>Best regards,<br>
                    <strong>EFRIS Platform Team</strong></p>
                </div>
                <div class="footer">
                    <p>© 2026 EFRIS Platform. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to EFRIS Platform!
        
        Hi {full_name},
        
        Your account has been created successfully!
        
        Login at: http://localhost:8001
        
        What's Next?
        1. Login to your dashboard
        2. Connect your ERP system (QuickBooks, Xero, or Zoho)
        3. Start fiscalizing invoices automatically
        
        Trial Period: You have a 2-day free trial to explore all features.
        
        Questions? Reply to this email!
        
        Best regards,
        EFRIS Platform Team
        """
        
        return self.send_email(to_email, subject, html_body, text_body)
    
    def send_client_approved_email(self, to_email: str, full_name: str, reseller_name: str):
        """Send email when owner approves a client"""
        subject = "Your EFRIS Account Has Been Activated!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #10b981; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1>✅ Account Activated!</h1>
                </div>
                <div style="background: #f9f9f9; padding: 30px;">
                    <p>Hi {full_name},</p>
                    
                    <p>Great news! Your EFRIS account has been approved and activated by our platform team.</p>
                    
                    <p><strong>Your Reseller:</strong> {reseller_name}</p>
                    
                    <p>You can now:</p>
                    <ul>
                        <li>Access your dashboard</li>
                        <li>Connect your ERP system</li>
                        <li>Fiscalize invoices to EFRIS</li>
                        <li>Manage your company settings</li>
                    </ul>
                    
                    <center>
                        <a href="http://localhost:8001/dashboard" style="display: inline-block; padding: 12px 30px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                            Login to Dashboard
                        </a>
                    </center>
                    
                    <p>Best regards,<br>
                    <strong>EFRIS Platform Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_body)
    
    def send_payment_confirmation(self, to_email: str, full_name: str, 
                                  amount: float, plan: str, end_date: datetime):
        """Send payment confirmation email"""
        subject = "Payment Received - Subscription Activated"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #667eea; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1>💳 Payment Confirmed!</h1>
                </div>
                <div style="background: #f9f9f9; padding: 30px;">
                    <p>Hi {full_name},</p>
                    
                    <p>Thank you for your payment! Your subscription has been activated.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <table style="width: 100%;">
                            <tr>
                                <td><strong>Plan:</strong></td>
                                <td>{plan.title()}</td>
                            </tr>
                            <tr>
                                <td><strong>Amount:</strong></td>
                                <td>UGX {amount:,.0f}</td>
                            </tr>
                            <tr>
                                <td><strong>Valid Until:</strong></td>
                                <td>{end_date.strftime('%B %d, %Y')}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <p>Your account now has full access to all premium features:</p>
                    <ul>
                        <li>Unlimited invoice fiscalization</li>
                        <li>Multiple ERP connections</li>
                        <li>Priority support</li>
                        <li>Advanced reporting</li>
                    </ul>
                    
                    <p>Invoice receipt attached (if applicable).</p>
                    
                    <center>
                        <a href="http://localhost:8001/dashboard" style="display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                            Go to Dashboard
                        </a>
                    </center>
                    
                    <p>Best regards,<br>
                    <strong>EFRIS Platform Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_body)
    
    def send_subscription_expiry_warning(self, to_email: str, full_name: str, days_left: int):
        """Send warning email before subscription expires"""
        subject = f"⚠️ Your Subscription Expires in {days_left} Days"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #f59e0b; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1>⚠️ Subscription Expiring Soon</h1>
                </div>
                <div style="background: #f9f9f9; padding: 30px;">
                    <p>Hi {full_name},</p>
                    
                    <p>This is a friendly reminder that your EFRIS Platform subscription will expire in 
                    <strong>{days_left} days</strong>.</p>
                    
                    <p>To continue enjoying uninterrupted service, please renew your subscription.</p>
                    
                    <center>
                        <a href="http://localhost:8001/dashboard?action=renew" style="display: inline-block; padding: 12px 30px; background: #10b981; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0;">
                            Renew Subscription
                        </a>
                    </center>
                    
                    <p><strong>What happens if I don't renew?</strong></p>
                    <ul>
                        <li>Your access will be suspended</li>
                        <li>Invoice fiscalization will stop</li>
                        <li>Your data will be preserved for 30 days</li>
                    </ul>
                    
                    <p>Questions? Reply to this email!</p>
                    
                    <p>Best regards,<br>
                    <strong>EFRIS Platform Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_body)
    
    def send_owner_notification(self, action: str, details: str, reseller_email: str = ""):
        """Send notification to platform owner about important events"""
        owner_email = os.getenv("OWNER_EMAIL", "owner@efrisplatform.com")
        subject = f"[EFRIS Platform] {action}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: monospace; padding: 20px;">
            <h2>Platform Event: {action}</h2>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Details:</strong> {details}</p>
            {f'<p><strong>Reseller:</strong> {reseller_email}</p>' if reseller_email else ''}
            
            <hr>
            <p><a href="http://localhost:8001/owner">View Owner Portal</a></p>
        </body>
        </html>
        """
        
        return self.send_email(owner_email, subject, html_body)


# Initialize email service
email_service = EmailService()

# Export
__all__ = ['email_service', 'EmailService']
