from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

import snitch
from snitch.models import AbstractNotification
from tests.app.events import (
    ACTIVATED_EVENT,
    CONFIRMED_EVENT,
    DUMMY_EVENT_NO_BODY,
    DYNAMIC_SPAM,
    LOCALIZED_EVENT,
    NO_SPAM,
    OTHER_DYNAMIC_SPAM,
    SMALL_EVENT,
    SPAM,
)


class Notification(AbstractNotification):
    """Custom notification."""

    extra_field = models.BooleanField(default=False)


class Stuff(models.Model):
    """Simple stuff model with status."""

    IDLE, ACTIVE, CONFIRMED = 0, 1, 2
    status = models.PositiveIntegerField(default=IDLE)
    activated_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    @snitch.dispatch(ACTIVATED_EVENT)
    def activate(self):
        self.activated_at = timezone.now()

    @snitch.dispatch(CONFIRMED_EVENT)
    def confirm(self):
        self.confirmed_at = timezone.now()

    @snitch.dispatch(SMALL_EVENT)
    def small(self):
        pass

    @snitch.dispatch(DUMMY_EVENT_NO_BODY)
    def dummy(self):
        pass

    @snitch.dispatch(SPAM, method=True, config={"kwargs": {"actor": "user"}})
    def spam(self, user):
        pass

    @snitch.dispatch(NO_SPAM, method=True, config={"kwargs": {"actor": "user"}})
    def no_spam(self, user):
        pass

    @snitch.dispatch(DYNAMIC_SPAM, method=True, config={"kwargs": {"actor": "user"}})
    def dynamic_spam(self, user):
        pass

    @snitch.dispatch(
        OTHER_DYNAMIC_SPAM, method=True, config={"kwargs": {"actor": "user"}}
    )
    def other_dynamic_spam(self, user):
        pass

    @snitch.dispatch(LOCALIZED_EVENT)
    def localized(self):
        pass


class Actor(models.Model):
    """Dummy actor."""


class Trigger(models.Model):
    """Dummy trigger."""


class Target(models.Model):
    """Dummy target."""


class OtherStuff(TimeStampedModel):
    """Other stuff."""
