from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException

from .config import get_settings


class ProcessRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int | None = None) -> None:
        settings = get_settings()
        max_attempts = limit or settings.rate_limit_max_attempts
        now = monotonic()
        window = settings.rate_limit_window_seconds
        events = self._events[key]
        while events and events[0] <= now - window:
            events.popleft()
        if len(events) >= max_attempts:
            reset = int(now + window)
            raise HTTPException(
                status_code=429,
                detail={'code': 'rate_limited', 'message': 'Muitas tentativas. Tente novamente em instantes.'},
                headers={'X-RateLimit-Limit': str(max_attempts), 'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(reset)},
            )
        events.append(now)


limiter = ProcessRateLimiter()
