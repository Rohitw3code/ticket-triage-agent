# agent/utils.py

import time
import logging
from typing import Callable, TypeVar, Any
from functools import wraps
from openai import APIError, APITimeoutError, RateLimitError, APIConnectionError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')


class LLMError(Exception):
    """Custom exception for LLM-related errors."""
    pass


def retry_with_backoff(
    max_retries: int = None,
    initial_delay: float = None,
    backoff_factor: float = None,
    exceptions: tuple = (APIError, APITimeoutError, RateLimitError, APIConnectionError)
):
    """
    Decorator to retry function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (uses config default if None)
        initial_delay: Initial delay between retries in seconds (uses config default if None)
        backoff_factor: Multiplier for delay on each retry (uses config default if None)
        exceptions: Tuple of exceptions to catch and retry
    """
    if max_retries is None:
        max_retries = settings.MAX_RETRIES
    if initial_delay is None:
        initial_delay = settings.RETRY_DELAY
    if backoff_factor is None:
        backoff_factor = settings.RETRY_BACKOFF
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise LLMError(
                            f"LLM call failed after {max_retries} retries: {str(e)}"
                        ) from e
                    
                    # Special handling for rate limits
                    if isinstance(e, RateLimitError):
                        logger.warning(
                            f"Rate limit hit for {func.__name__}, "
                            f"waiting {delay}s before retry {attempt + 1}/{max_retries}"
                        )
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                    
                    time.sleep(delay)
                    delay *= backoff_factor
                    
                except Exception as e:
                    # Don't retry on unexpected exceptions
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


async def retry_with_backoff_async(
    max_retries: int = None,
    initial_delay: float = None,
    backoff_factor: float = None,
    exceptions: tuple = (APIError, APITimeoutError, RateLimitError, APIConnectionError)
):
    """
    Async version of retry_with_backoff decorator.
    """
    import asyncio
    
    if max_retries is None:
        max_retries = settings.MAX_RETRIES
    if initial_delay is None:
        initial_delay = settings.RETRY_DELAY
    if backoff_factor is None:
        backoff_factor = settings.RETRY_BACKOFF
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise LLMError(
                            f"LLM call failed after {max_retries} retries: {str(e)}"
                        ) from e
                    
                    if isinstance(e, RateLimitError):
                        logger.warning(
                            f"Rate limit hit for {func.__name__}, "
                            f"waiting {delay}s before retry {attempt + 1}/{max_retries}"
                        )
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay}s..."
                        )
                    
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                    
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    raise
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def handle_llm_error(error: Exception) -> dict:
    """
    Convert LLM errors to user-friendly messages.
    
    Args:
        error: The exception that was raised
        
    Returns:
        dict with error type and message
    """
    if isinstance(error, RateLimitError):
        return {
            "error": "rate_limit",
            "message": "API rate limit exceeded. Please try again in a moment.",
            "retry_after": getattr(error, 'retry_after', 60)
        }
    
    elif isinstance(error, APITimeoutError):
        return {
            "error": "timeout",
            "message": "Request timed out. Please try again.",
        }
    
    elif isinstance(error, APIConnectionError):
        return {
            "error": "connection",
            "message": "Unable to connect to AI service. Please check your internet connection.",
        }
    
    elif isinstance(error, APIError):
        return {
            "error": "api_error",
            "message": f"AI service error: {str(error)}",
        }
    
    elif isinstance(error, LLMError):
        return {
            "error": "llm_error",
            "message": str(error),
        }
    
    else:
        return {
            "error": "unknown",
            "message": "An unexpected error occurred. Please try again.",
        }
