from django.db import models
from django.utils import timezone
from model_utils.models import TimeStampedModel

import snitch
from snitch.models import AbstractNotification
from tests.app.events import ACTIVATED_EVENT, CONFIRMED_EVENT


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


class Actor(models.Model):
    """Dummy actor."""

    pass


class Trigger(models.Model):
    """Dummy trigger."""

    pass


class Target(models.Model):
    """Dummy target."""

    pass


class OtherStuff(TimeStampedModel):
    """Other stuff."""

    pass
