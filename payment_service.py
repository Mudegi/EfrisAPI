"""
Payment Integration Service
Handles Flutterwave payment processing for subscription upgrades
"""
import os
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class FlutterwavePayment:
    """Handle Flutterwave payment processing"""
    
    def __init__(self):
        self.secret_key = os.getenv("FLUTTERWAVE_SECRET_KEY", "")
        self.public_key = os.getenv("FLUTTERWAVE_PUBLIC_KEY", "")
        self.base_url = "https://api.flutterwave.com/v3"
        self.webhook_secret = os.getenv("FLUTTERWAVE_WEBHOOK_SECRET", "")
    
    def initialize_payment(self, user_email: str, user_name: str, amount: float, 
                          user_id: int, plan: str = "annual") -> Dict[str, Any]:
        """
        Initialize payment transaction
        
        Args:
            user_email: User's email
            user_name: User's full name
            amount: Amount in UGX
            user_id: Database user ID
            plan: Subscription plan (annual, monthly, etc.)
        
        Returns:
            Dictionary with payment link and transaction reference
        """
        payload = {
            "tx_ref": f"EFRIS-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "amount": amount,
            "currency": "UGX",
            "redirect_url": os.getenv("PAYMENT_REDIRECT_URL", "http://localhost:8001/payment/callback"),
            "payment_options": "mobilemoney,card",
            "customer": {
                "email": user_email,
                "name": user_name
            },
            "customizations": {
                "title": "EFRIS SaaS Subscription",
                "description": f"{plan.title()} Subscription Payment",
                "logo": os.getenv("COMPANY_LOGO_URL", "")
            },
            "meta": {
                "user_id": user_id,
                "plan": plan
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                return {
                    "success": True,
                    "payment_link": data["data"]["link"],
                    "tx_ref": payload["tx_ref"]
                }
            else:
                return {
                    "success": False,
                    "error": data.get("message", "Payment initialization failed")
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Payment API error: {str(e)}"
            }
    
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify payment transaction
        
        Args:
            transaction_id: Flutterwave transaction ID
        
        Returns:
            Dictionary with verification status and details
        """
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/transactions/{transaction_id}/verify",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success":
                return {
                    "success": True,
                    "data": data["data"]
                }
            else:
                return {
                    "success": False,
                    "error": data.get("message", "Verification failed")
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Verification API error: {str(e)}"
            }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from Flutterwave
        
        Args:
            payload: Raw webhook payload string
            signature: Signature from webhook header
        
        Returns:
            Boolean indicating if signature is valid
        """
        if not self.webhook_secret:
            return False
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)


class PaymentManager:
    """Manage subscription payments and upgrades"""
    
    @staticmethod
    def calculate_subscription_end(plan: str = "annual") -> datetime:
        """Calculate subscription end date based on plan"""
        now = datetime.now()
        if plan == "annual":
            return now + timedelta(days=365)
        elif plan == "monthly":
            return now + timedelta(days=30)
        elif plan == "quarterly":
            return now + timedelta(days=90)
        else:
            return now + timedelta(days=365)  # Default to annual
    
    @staticmethod
    def get_plan_price(plan: str = "annual") -> float:
        """Get price for subscription plan in UGX"""
        prices = {
            "annual": 500000,  # UGX 500,000
            "quarterly": 150000,  # UGX 150,000
            "monthly": 60000    # UGX 60,000
        }
        return prices.get(plan, 500000)
    
    @staticmethod
    def activate_subscription(db, user_id: int, plan: str = "annual", 
                             transaction_ref: Optional[str] = None) -> bool:
        """
        Activate user subscription after successful payment
        
        Args:
            db: Database session
            user_id: User ID to activate
            plan: Subscription plan
            transaction_ref: Payment transaction reference
        
        Returns:
            Boolean indicating success
        """
        from database.models import User, ActivityLog
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # Update subscription
            user.subscription_status = "active"
            user.subscription_ends = PaymentManager.calculate_subscription_end(plan)
            user.status = "active"
            user.is_active = True
            
            # Increase client limit for resellers
            if user.role == "reseller":
                if plan == "annual":
                    user.max_clients = 20
                elif plan == "quarterly":
                    user.max_clients = 10
                else:
                    user.max_clients = 5
            
            # Log activity
            activity = ActivityLog(
                user_id=user_id,
                action=f"subscription_activated_{plan}",
                details=f"Payment received - {plan} plan",
                document_number=transaction_ref
            )
            db.add(activity)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"Error activating subscription: {e}")
            return False


# Initialize payment service
flutterwave = FlutterwavePayment()
payment_manager = PaymentManager()
