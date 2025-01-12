import asyncio
from typing import Dict, Any
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(
        self, 
        max_calls: int = 10, 
        period: timedelta = timedelta(minutes=1)
    ):
        """
        Initialize rate limiter
        
        :param max_calls: Maximum number of calls allowed in the given period
        :param period: Time window for rate limiting
        """
        self.max_calls = max_calls
        self.period = period
        self._calls: Dict[str, list] = {}

    def _cleanup_old_calls(self, key: str):
        """
        Remove calls older than the specified period
        
        :param key: Unique identifier for the rate limit group
        """
        now = datetime.now()
        self._calls[key] = [
            call_time for call_time in self._calls.get(key, [])
            if now - call_time < self.period
        ]

    def is_allowed(self, key: str) -> bool:
        """
        Check if a call is allowed
        
        :param key: Unique identifier for the rate limit group
        :return: Boolean indicating if the call is allowed
        """
        now = datetime.now()
        
        # Cleanup old calls
        self._cleanup_old_calls(key)
        
        # Check if within rate limit
        if len(self._calls.get(key, [])) < self.max_calls:
            # Record the call
            if key not in self._calls:
                self._calls[key] = []
            self._calls[key].append(now)
            return True
        
        return False

    async def wait_and_execute(
        self, 
        key: str, 
        func: Any, 
        *args, 
        **kwargs
    ):
        """
        Wait and execute a function if rate limit allows
        
        :param key: Unique identifier for the rate limit group
        :param func: Function to execute
        :param args: Positional arguments for the function
        :param kwargs: Keyword arguments for the function
        :return: Result of the function
        """
        while not self.is_allowed(key):
            await asyncio.sleep(1)  # Wait if rate limited
        
        return await func(*args, **kwargs)

    def get_remaining_calls(self, key: str) -> int:
        """
        Get remaining calls for a specific key
        
        :param key: Unique identifier for the rate limit group
        :return: Number of remaining calls
        """
        self._cleanup_old_calls(key)
        return max(0, self.max_calls - len(self._calls.get(key, [])))

    def reset_key(self, key: str):
        """
        Reset calls for a specific key
        
        :param key: Unique identifier for the rate limit group
        """
        if key in self._calls:
            del self._calls[key]
