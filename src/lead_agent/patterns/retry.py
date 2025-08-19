"""Retry pattern implementation with exponential backoff."""

import asyncio
import random
import time
from typing import Any, Callable, TypeVar

from ..models import RetryConfig

T = TypeVar('T')


class RetryExhaustedException(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class RetryHandler:
    """Handles retry logic with exponential backoff and jitter."""
    
    def __init__(self, config: RetryConfig):
        """Initialize retry handler.
        
        Args:
            config: Retry configuration
        """
        self.config = config
    
    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Result of function execution
            
        Raises:
            RetryExhaustedException: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                
                # Don't retry on last attempt
                if attempt == self.config.max_attempts - 1:
                    break
                
                # Calculate delay with exponential backoff
                delay = self._calculate_delay(attempt)
                await asyncio.sleep(delay)
        
        # All attempts failed
        raise RetryExhaustedException(
            f"All {self.config.max_attempts} retry attempts failed. "
            f"Last error: {last_exception}"
        )
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Exponential backoff: initial_delay * (base ^ attempt)
        delay = self.config.initial_delay * (
            self.config.exponential_base ** attempt
        )
        
        # Cap at max_delay
        delay = min(delay, self.config.max_delay)
        
        # Add jitter to avoid thundering herd
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            jitter = random.uniform(-jitter_range, jitter_range)
            delay += jitter
        
        return max(0, delay)  # Ensure non-negative delay
