import hashlib
from typing import TYPE_CHECKING, Any, Callable

from django.core.cache import caches
from django.db import models

if TYPE_CHECKING:
    from snitch.handlers import EventHandler


class AbstractCoolDownManager:
    """The cool down manager handles the cool down feature for notifications, to avoid
    sending several notifications to the same user."""

    event_handler: "EventHandler"

    def __init__(self, event_handler: "EventHandler") -> None:
        self.event_handler = event_handler

    def should_notify(self, receiver: models.Model) -> bool:
        """By default, always notify."""
        return True

    def should_send(self, receiver: models.Model) -> bool:
        """By default, always send."""
        return True


class CoolDownManager(AbstractCoolDownManager):
    """This cool down manager uses the default cache from django to handle the number
    of attempts and the cool down time.
    """

    prefix: str = "snitch"
    cache_alias: str
    attempts: int | Callable[["models.Model"], int] | str
    timeout: int | Callable[["models.Model"], int] | str

    def __init__(self, event_handler: "EventHandler") -> None:
        self.event_handler = event_handler
        self.attempts = getattr(event_handler, "cool_down_attempts", 1)
        self.timeout = getattr(event_handler, "cool_down_time", 0)
        self.cache_alias = getattr(event_handler, "cool_down_cache_alias", "default")

    @property
    def _cache(self) -> Any:
        """Gets the cache proxy using the alias."""
        return caches[self.cache_alias]

    def _key(self, receiver: "models.Model", suffix: str = "") -> str:
        """Get the cache key used by the cool down manager."""
        if receiver.pk is None:
            raise AttributeError("The receiver should have a primary key.")
        key = f"{self.prefix}-cool-down-{self.event_handler.event.verb}-{receiver._meta.app_label}-{receiver._meta.model_name}-{receiver.pk}"
        if suffix:
            key = f"{key}-{suffix}"
        # Use hash function to ensure compatibility
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return hashed_key

    def _timeout(self, receiver: "models.Model") -> int:
        """Gets the timeout of the cache in seconds, using the time of the cool down.
        If the timeout is a callable, calls the function, passing the receiver.
        """
        if callable(self.timeout):
            return self.timeout(receiver)
        if isinstance(self.timeout, str):
            return getattr(self.event_handler, self.timeout)(receiver)
        return self.timeout

    def _attempts(self, receiver: "models.Model") -> int:
        """Gets the number of attempts, using the time of the cool down. If the
        attempts number is a callable, calls the function, passing the receiver.
        """
        if callable(self.attempts):
            return self.attempts(receiver)
        if isinstance(self.attempts, str):
            return getattr(self.event_handler, self.attempts)(receiver)
        return self.attempts

    def _check_cool_down(self, receiver: models.Model, suffix: str = "") -> bool:
        """Checks the cool down for the receiver."""
        key = self._key(receiver=receiver, suffix=suffix)
        try:
            self._cache.get_or_set(key, 0, self._timeout(receiver=receiver))
            counter = self._cache.incr(key)
        except ValueError:
            counter = 1
        return counter <= self._attempts(receiver=receiver)

    def should_notify(self, receiver: models.Model) -> bool:
        """Uses the default cool down by default."""
        return self._check_cool_down(receiver=receiver, suffix="notify")

    def should_send(self, receiver: models.Model) -> bool:
        """By default, always send."""
        return self._check_cool_down(receiver=receiver, suffix="send")
