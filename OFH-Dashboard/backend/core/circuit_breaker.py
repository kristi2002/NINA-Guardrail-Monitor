#!/usr/bin/env python3
"""Circuit breaker utilities for external integrations."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, Optional, Tuple, Type, Union


class CircuitBreakerOpenError(RuntimeError):
    """Raised when the circuit breaker is open and calls are not permitted."""

    def __init__(self, message: str, *, name: Optional[str] = None, opened_at: Optional[datetime] = None) -> None:
        suffix = f" (breaker: {name})" if name else ""
        details = f" Circuit opened at {opened_at.isoformat()}" if opened_at else ""
        super().__init__(f"{message}{suffix}{details}")
        self.name = name
        self.opened_at = opened_at


@dataclass
class CircuitBreakerState:
    """Internal state snapshot for a circuit breaker."""

    name: str
    state: str
    failure_count: int
    opened_at: Optional[datetime]
    last_failure: Optional[datetime]
    last_exception: Optional[BaseException]


class CircuitBreaker:
    """Simple thread-safe circuit breaker implementation."""

    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half_open"

    def __init__(
        self,
        *,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: Union[int, float] = 60,
        expected_exception: Union[Type[BaseException], Tuple[Type[BaseException], ...]] = Exception,
        half_open_max_successes: int = 1,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")
        if isinstance(expected_exception, Iterable) and not isinstance(expected_exception, tuple):
            expected_exception = tuple(expected_exception)  # type: ignore[assignment]

        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_successes = max(1, half_open_max_successes)

        self._state = self.STATE_CLOSED
        self._failure_count = 0
        self._consecutive_half_open_successes = 0
        self._opened_at: Optional[datetime] = None
        self._last_failure: Optional[datetime] = None
        self._last_exception: Optional[BaseException] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def current_state(self) -> CircuitBreakerState:
        with self._lock:
            return CircuitBreakerState(
                name=self.name,
                state=self._state,
                failure_count=self._failure_count,
                opened_at=self._opened_at,
                last_failure=self._last_failure,
                last_exception=self._last_exception,
            )

    def is_open(self) -> bool:
        return self.current_state().state == self.STATE_OPEN

    def is_half_open(self) -> bool:
        return self.current_state().state == self.STATE_HALF_OPEN

    def is_closed(self) -> bool:
        return self.current_state().state == self.STATE_CLOSED

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def before_call(self) -> None:
        """Check if a call is allowed; update state if timeout expired."""

        with self._lock:
            if self._state == self.STATE_OPEN:
                assert self._opened_at is not None  # for mypy
                elapsed = datetime.utcnow() - self._opened_at
                if elapsed >= timedelta(seconds=self.recovery_timeout):
                    # Move to half-open to test the waters
                    self._state = self.STATE_HALF_OPEN
                    self._consecutive_half_open_successes = 0
                else:
                    raise CircuitBreakerOpenError(
                        "Circuit breaker is open; skipping call",
                        name=self.name,
                        opened_at=self._opened_at,
                    )

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._last_exception = None
            self._last_failure = None

            if self._state == self.STATE_HALF_OPEN:
                self._consecutive_half_open_successes += 1
                if self._consecutive_half_open_successes >= self.half_open_max_successes:
                    self._state = self.STATE_CLOSED
                    self._opened_at = None
            else:
                self._state = self.STATE_CLOSED
                self._opened_at = None

    def record_failure(self, exc: Optional[BaseException] = None) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure = datetime.utcnow()
            self._last_exception = exc

            if self._failure_count >= self.failure_threshold:
                self._state = self.STATE_OPEN
                self._opened_at = datetime.utcnow()
                self._consecutive_half_open_successes = 0

    def reset(self) -> None:
        with self._lock:
            self._state = self.STATE_CLOSED
            self._failure_count = 0
            self._consecutive_half_open_successes = 0
            self._opened_at = None
            self._last_failure = None
            self._last_exception = None

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call a function within the circuit breaker guard."""

        self.before_call()
        try:
            result = func(*args, **kwargs)
        except self.expected_exception as exc:  # type: ignore[misc]
            self.record_failure(exc)
            raise
        except BaseException as exc:
            # Treat unexpected exceptions as failures as well
            self.record_failure(exc)
            raise
        else:
            self.record_success()
            return result

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator form for circuit breaker."""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self.call(func, *args, **kwargs)

        return wrapper


