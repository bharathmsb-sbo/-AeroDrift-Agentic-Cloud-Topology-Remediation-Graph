"""
Retry Logic and Resilience Patterns for AeroDrift.

This module provides retry mechanisms, circuit breakers, and resilience
patterns for handling transient failures in external API calls.
"""

import logging
import time
import random
from typing import Callable, Optional, Type, Tuple, Any
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategies for different failure scenarios."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    IMMEDIATE = "immediate"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.
    
    Stops calling failing services after a threshold of failures
    and allows a limited number of test calls to check for recovery.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
                logger.info("Circuit breaker transitioning to half-open state")
            else:
                raise Exception("Circuit breaker is OPEN - calls are blocked")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful function call."""
        self.failure_count = 0
        if self.state == "half_open":
            self.state = "closed"
            logger.info("Circuit breaker reset to closed state")
    
    def _on_failure(self):
        """Handle failed function call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    jitter_factor: float = 0.1,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Decorator for retrying functions with configurable backoff strategy.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        jitter_factor: Factor for jitter calculation
        strategy: Retry strategy to use
        retryable_exceptions: Exceptions that should trigger retry
        non_retryable_exceptions: Exceptions that should not trigger retry
        on_retry: Callback function called on each retry (attempt, exception)
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                jitter_factor=jitter_factor,
                strategy=strategy,
                retryable_exceptions=retryable_exceptions or (Exception,),
                non_retryable_exceptions=non_retryable_exceptions or ()
            )
            
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.non_retryable_exceptions as e:
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}")
                        raise
                    
                    delay = _calculate_delay(attempt, config)
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    jitter_factor: float = 0.1,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    non_retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    Decorator for retrying async functions with configurable backoff strategy.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        jitter_factor: Factor for jitter calculation
        strategy: Retry strategy to use
        retryable_exceptions: Exceptions that should trigger retry
        non_retryable_exceptions: Exceptions that should not trigger retry
        on_retry: Callback function called on each retry (attempt, exception)
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter,
                jitter_factor=jitter_factor,
                strategy=strategy,
                retryable_exceptions=retryable_exceptions or (Exception,),
                non_retryable_exceptions=non_retryable_exceptions or ()
            )
            
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.non_retryable_exceptions as e:
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(f"Max retry attempts ({config.max_attempts}) reached for {func.__name__}")
                        raise
                    
                    delay = _calculate_delay(attempt, config)
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay based on retry strategy.
    
    Args:
        attempt: Current attempt number
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    if config.strategy == RetryStrategy.IMMEDIATE:
        delay = 0
    elif config.strategy == RetryStrategy.FIXED_DELAY:
        delay = config.base_delay
    elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
        delay = config.base_delay * (attempt + 1)
    else:  # EXPONENTIAL_BACKOFF
        delay = config.base_delay * (config.exponential_base ** attempt)
    
    # Apply max delay limit
    delay = min(delay, config.max_delay)
    
    # Add jitter if enabled
    if config.jitter and delay > 0:
        jitter_amount = delay * config.jitter_factor
        delay = delay + random.uniform(-jitter_amount, jitter_amount)
        delay = max(0, delay)  # Ensure non-negative
    
    return delay


class RetryTracker:
    """
    Track retry statistics for monitoring and analysis.
    """
    
    def __init__(self):
        """Initialize retry tracker."""
        self._attempts: Dict[str, int] = {}
        self._successes: Dict[str, int] = {}
        self._failures: Dict[str, int] = {}
        self._total_delays: Dict[str, float] = {}
    
    def record_attempt(self, operation: str):
        """Record a retry attempt for an operation."""
        self._attempts[operation] = self._attempts.get(operation, 0) + 1
    
    def record_success(self, operation: str):
        """Record a successful retry for an operation."""
        self._successes[operation] = self._successes.get(operation, 0) + 1
    
    def record_failure(self, operation: str):
        """Record a failed retry for an operation."""
        self._failures[operation] = self._failures.get(operation, 0) + 1
    
    def record_delay(self, operation: str, delay: float):
        """Record delay time for an operation."""
        self._total_delays[operation] = self._total_delays.get(operation, 0.0) + delay
    
    def get_statistics(self, operation: str) -> Dict[str, Any]:
        """
        Get retry statistics for an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            Dictionary with retry statistics
        """
        attempts = self._attempts.get(operation, 0)
        successes = self._successes.get(operation, 0)
        failures = self._failures.get(operation, 0)
        total_delay = self._total_delays.get(operation, 0.0)
        
        return {
            'operation': operation,
            'total_attempts': attempts,
            'successes': successes,
            'failures': failures,
            'success_rate': (successes / attempts * 100) if attempts > 0 else 0,
            'total_delay_seconds': total_delay,
            'average_delay_seconds': (total_delay / attempts) if attempts > 0 else 0
        }
    
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all tracked operations.
        
        Returns:
            Dictionary mapping operation names to their statistics
        """
        all_operations = set(self._attempts.keys()) | set(self._successes.keys()) | set(self._failures.keys())
        return {op: self.get_statistics(op) for op in all_operations}


# Global retry tracker instance
global_retry_tracker = RetryTracker()