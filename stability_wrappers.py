"""
Stability Wrappers - Prevent API crashes under load
Provides database error handling, timeouts, and retry logic
"""
from functools import wraps
from sqlalchemy.orm import Session
from fastapi import HTTPException
import traceback
from typing import Callable, Any
from monitoring import logger, error_monitor


def with_db_error_handling(func: Callable) -> Callable:
    """
    Wrapper to ensure database rollback on exceptions
    CRITICAL: Prevents connection leaks that kill the API
    
    Usage:
        @with_db_error_handling
        async def my_endpoint(db: Session = Depends(get_db)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        db: Session = None
        
        # Extract db session from kwargs
        if 'db' in kwargs:
            db = kwargs['db']
        
        try:
            result = await func(*args, **kwargs)
            return result
        except HTTPException:
            # Let HTTP exceptions pass through (they're intentional)
            if db:
                db.rollback()
            raise
        except Exception as e:
            # Catch all other exceptions
            if db:
                db.rollback()
            
            # Log the error
            error_monitor.capture_exception(e, {
                "function": func.__name__,
                "args": str(args)[:200],
                "kwargs": str(kwargs)[:200]
            })
            
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return generic error to client
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in {func.__name__}"
            )
    
    return wrapper


def with_db_error_handling_sync(func: Callable) -> Callable:
    """Synchronous version of database error handler"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        db: Session = None
        
        if 'db' in kwargs:
            db = kwargs['db']
        
        try:
            result = func(*args, **kwargs)
            return result
        except HTTPException:
            if db:
                db.rollback()
            raise
        except Exception as e:
            if db:
                db.rollback()
            
            error_monitor.capture_exception(e, {
                "function": func.__name__,
            })
            
            logger.error(f"Error in {func.__name__}: {str(e)}")
            
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in {func.__name__}"
            )
    
    return wrapper


class TimeoutException(Exception):
    """Raised when operation times out"""
    pass


def ensure_db_rollback(db: Session):
    """
    Manually ensure database rollback
    Use in finally blocks or exception handlers
    
    Usage:
        try:
            db.commit()
        except Exception as e:
            ensure_db_rollback(db)
            raise
    """
    try:
        if db:
            db.rollback()
            logger.debug("Database rolled back")
    except Exception as e:
        logger.error(f"Error during rollback: {e}")


def safe_commit(db: Session) -> bool:
    """
    Safely commit database transaction with error handling
    
    Returns:
        Boolean indicating success
    
    Usage:
        if safe_commit(db):
            return {"success": True}
        else:
            raise HTTPException(500, "Failed to save")
    """
    try:
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Commit failed: {e}")
        ensure_db_rollback(db)
        error_monitor.capture_exception(e)
        return False


def with_timeout(seconds: int):
    """
    Decorator to add timeout to function execution
    CRITICAL: Prevents hung operations from blocking workers
    
    Usage:
        @with_timeout(30)
        async def slow_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds}s")
                raise HTTPException(
                    status_code=504,
                    detail=f"Operation timed out after {seconds} seconds"
                )
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for external services (EFRIS)
    Prevents cascading failures when external service is down
    
    States:
    - CLOSED: Normal operation
    - OPEN: Service is down, reject all requests
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Usage:
            circuit_breaker = CircuitBreaker()
            result = circuit_breaker.call(make_efris_request, url, data)
        """
        import time
        
        # Check if circuit is open
        if self.state == "OPEN":
            # Check if timeout period has passed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: HALF_OPEN - testing service")
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable. Please try again later."
                )
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset failures
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
                logger.info("Circuit breaker: CLOSED - service recovered")
            
            return result
        
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            # Open circuit if threshold reached
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker: OPEN - service failed {self.failures} times")
            
            raise


# Global circuit breaker for EFRIS
efris_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)


# Export all utilities
__all__ = [
    'with_db_error_handling',
    'with_db_error_handling_sync',
    'ensure_db_rollback',
    'safe_commit',
    'with_timeout',
    'CircuitBreaker',
    'efris_circuit_breaker'
]
