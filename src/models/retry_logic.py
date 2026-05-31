# src/models/retry_logic.py

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import litellm

def get_retry_decorator(max_attempts: int = 4):
    """
    Creates a retry decorator that handles API failures, rate limits, and timeouts.
    It waits exponentially between retries (e.g., 2s, 4s, 8s...).
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((
            litellm.exceptions.RateLimitError,
            litellm.exceptions.ServiceUnavailableError,
            litellm.exceptions.Timeout,
            litellm.exceptions.APIConnectionError,
            litellm.exceptions.APIError
        )),
        reraise=True
    )