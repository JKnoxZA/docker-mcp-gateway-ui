"""Retry utility for handling transient failures"""

import asyncio
import functools
import logging
import random
from typing import Callable, Optional, Tuple, Type, Union

logger = logging.getLogger(__name__)


def retry_async(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    condition: Optional[Callable[[Exception], bool]] = None,
):
    """
    Async retry decorator with exponential backoff and jitter

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for exponential backoff
        jitter: Add random jitter to delay
        exceptions: Exception types to catch and retry
        condition: Optional function to determine if exception should be retried
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if condition and not condition(e):
                        logger.debug(f"Exception {e} failed retry condition, not retrying")
                        raise

                    # Don't delay on the last attempt
                    if attempt == max_attempts - 1:
                        break

                    # Calculate delay with optional jitter
                    actual_delay = current_delay
                    if jitter:
                        actual_delay *= (0.5 + random.random())

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )

                    await asyncio.sleep(actual_delay)
                    current_delay *= backoff

            # All attempts failed
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception

        return wrapper
    return decorator


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
):
    """
    Circuit breaker pattern to prevent cascading failures

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting to close circuit
        expected_exception: Exception type that counts as failure
    """
    def decorator(func):
        state = {
            'failure_count': 0,
            'last_failure_time': None,
            'state': 'closed'  # closed, open, half-open
        }

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import time

            current_time = time.time()

            # Check if circuit should transition from open to half-open
            if (state['state'] == 'open' and
                state['last_failure_time'] and
                current_time - state['last_failure_time'] >= recovery_timeout):
                state['state'] = 'half-open'
                logger.info(f"Circuit breaker for {func.__name__} transitioning to half-open")

            # Reject calls if circuit is open
            if state['state'] == 'open':
                raise Exception(f"Circuit breaker is open for {func.__name__}")

            try:
                result = await func(*args, **kwargs)

                # Success - reset failure count and close circuit
                if state['state'] == 'half-open':
                    logger.info(f"Circuit breaker for {func.__name__} closing after successful call")
                state['failure_count'] = 0
                state['state'] = 'closed'
                return result

            except expected_exception as e:
                state['failure_count'] += 1
                state['last_failure_time'] = current_time

                # Open circuit if threshold exceeded
                if state['failure_count'] >= failure_threshold:
                    state['state'] = 'open'
                    logger.error(
                        f"Circuit breaker opened for {func.__name__} after "
                        f"{state['failure_count']} failures"
                    )

                raise

        return wrapper
    return decorator