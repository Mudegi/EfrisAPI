"""
Error Monitoring and Logging Service
Provides structured logging and error tracking for production
"""
import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "efris_api.log")

# Create logger
logger = logging.getLogger("efris_api")
logger.setLevel(getattr(logging, LOG_LEVEL))

# File handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter(
    '%(levelname)s: %(message)s'
)
console_handler.setFormatter(console_formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class ErrorMonitor:
    """Monitor and track errors in production"""
    
    def __init__(self):
        self.sentry_enabled = os.getenv("SENTRY_DSN", "") != ""
        
        if self.sentry_enabled:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.fastapi import FastAPIIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                
                sentry_sdk.init(
                    dsn=os.getenv("SENTRY_DSN"),
                    environment=os.getenv("APP_ENV", "development"),
                    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
                    integrations=[
                        FastAPIIntegration(),
                        SqlalchemyIntegration()
                    ]
                )
                logger.info("Sentry error monitoring initialized")
            except ImportError:
                logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk")
                self.sentry_enabled = False
    
    def capture_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Capture exception and send to monitoring service
        
        Args:
            error: The exception to capture
            context: Additional context (user_id, company_id, etc.)
        """
        # Log locally
        logger.error(f"Exception: {str(error)}", exc_info=True)
        
        # Send to Sentry if enabled
        if self.sentry_enabled:
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if context:
                        for key, value in context.items():
                            scope.set_tag(key, value)
                    sentry_sdk.capture_exception(error)
            except Exception as e:
                logger.error(f"Failed to send to Sentry: {e}")
    
    def log_activity(self, user_id: Optional[int], action: str, details: str, 
                    company_id: Optional[int] = None, document_number: Optional[str] = None):
        """
        Log user activity for audit trail
        
        Args:
            user_id: ID of user performing action
            action: Action type (e.g., 'invoice_fiscalized', 'login', 'company_created')
            details: Detailed description
            company_id: Related company ID
            document_number: Related document (invoice number, etc.)
        """
        log_message = f"USER:{user_id} | ACTION:{action} | DETAILS:{details}"
        if company_id:
            log_message += f" | COMPANY:{company_id}"
        if document_number:
            log_message += f" | DOC:{document_number}"
        
        logger.info(log_message)
        
        # Also store in database if session available
        try:
            from database.connection import SessionLocal
            from database.models import ActivityLog
            
            db = SessionLocal()
            activity = ActivityLog(
                user_id=user_id,
                company_id=company_id,
                action=action,
                details=details,
                document_number=document_number
            )
            db.add(activity)
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"Failed to save activity to database: {e}")


def log_errors(func):
    """
    Decorator to automatically log errors from functions
    
    Usage:
        @log_errors
        async def my_endpoint():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_monitor.capture_exception(e, {
                "function": func.__name__,
                "args": str(args)[:200],  # Limit to 200 chars
            })
            raise
    return wrapper


def log_errors_sync(func):
    """Decorator for synchronous functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_monitor.capture_exception(e, {
                "function": func.__name__,
                "args": str(args)[:200],
            })
            raise
    return wrapper


class PerformanceMonitor:
    """Monitor API performance and slow queries"""
    
    def __init__(self):
        self.slow_query_threshold = float(os.getenv("SLOW_QUERY_THRESHOLD", "2.0"))  # seconds
    
    def log_slow_query(self, query: str, duration: float, context: Optional[Dict] = None):
        """Log slow database queries"""
        if duration > self.slow_query_threshold:
            logger.warning(
                f"SLOW QUERY ({duration:.2f}s): {query[:200]}... | Context: {context}"
            )


# Initialize monitors
error_monitor = ErrorMonitor()
performance_monitor = PerformanceMonitor()


# Export for use in other modules
__all__ = [
    'logger',
    'error_monitor',
    'performance_monitor',
    'log_errors',
    'log_errors_sync'
]
