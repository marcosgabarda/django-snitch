import io

from django.contrib.auth import get_user_model
from django.db import models

import snitch
from snitch.backends import EmailNotificationBackend, PushNotificationBackend

ACTIVATED_EVENT = "activated"
CONFIRMED_EVENT = "confirmed"
DUMMY_EVENT = "dummy"
DUMMY_EVENT_ASYNC = "dummy async"
EVERY_HOUR = "every hour"
SMALL_EVENT = "small"
DUMMY_EVENT_NO_BODY = "dummy no body"
SPAM = "spam"
NO_SPAM = "no spam"
DYNAMIC_SPAM = "dynamic spam"
OTHER_DYNAMIC_SPAM = "other dynamic spam"


@snitch.register(ACTIVATED_EVENT)
class ActivatedHandler(snitch.EventHandler):
    title = "Activated!"

    notification_backends = [PushNotificationBackend, EmailNotificationBackend]

    # Custom configuration for email backend
    template_email_kwargs = {"template_name": "email.html"}


@snitch.register(CONFIRMED_EVENT)
class ConfirmedHandler(snitch.EventHandler):
    title = "Confirmed!"
    notification_backends = [PushNotificationBackend, EmailNotificationBackend]

    # Custom configuration for email backend
    template_email_kwargs = {"template_name": "email.html"}

    def audience(self):
        return get_user_model().objects.all()

    def get_email_subject(self):
        return "Subject"

    def get_email_extra_context(self):
        return {"user": 1}

    def get_email_kwargs_attr(self):
        return {
            "template_name": "email.html",
            "attaches": [("dummy.txt", io.StringIO("dummy"), "text/plain")],
        }


@snitch.register(DUMMY_EVENT_ASYNC)
class DummyAsyncHandler(snitch.EventHandler):
    title = "Dummy event"
    delay = 60
    notification_creation_async = True

    def audience(self):
        return get_user_model().objects.all()


@snitch.register(DUMMY_EVENT)
class DummyHandler(snitch.EventHandler):
    title = "Dummy event"
    delay = 60


@snitch.register(EVERY_HOUR)
class EveryHourHandler(snitch.EventHandler):
    title = "Every hour event"


@snitch.register(SMALL_EVENT)
class SmallHandler(snitch.EventHandler):
    ephemeral = True
    notification_backends = [EmailNotificationBackend]
    title = "Small event!"
    template_email_kwargs = {"template_name": "email.html"}


@snitch.register(DUMMY_EVENT_NO_BODY)
class DummyNoBodyHandler(snitch.EventHandler):
    def get_title(self) -> str | None:
        return None

    def get_text(self) -> str | None:
        return None


@snitch.register(SPAM)
class SpamHandler(snitch.EventHandler):
    cool_down_manager_class = snitch.CoolDownManager
    cool_down_attempts = 5
    cool_down_time = 5
    notification_backends = [PushNotificationBackend]

    def audience(self):
        return get_user_model().objects.all()


@snitch.register(NO_SPAM)
class NoSpamHandler(snitch.EventHandler):
    cool_down_manager_class = snitch.CoolDownManager
    cool_down_attempts = 1
    cool_down_time = 0
    notification_backends = [PushNotificationBackend]

    def audience(self):
        return get_user_model().objects.all()


def dynamic_cool_down_attempts(
    event_handler: snitch.EventHandler, receiver: models.Model
):
    return 5


def dynamic_cool_down_time(event_handler: snitch.EventHandler, receiver: models.Model):
    return 5


@snitch.register(DYNAMIC_SPAM)
class DynamicSpamHandler(snitch.EventHandler):
    cool_down_manager_class = snitch.CoolDownManager
    cool_down_attempts = dynamic_cool_down_attempts
    cool_down_time = dynamic_cool_down_time
    notification_backends = [PushNotificationBackend]

    def audience(self):
        return get_user_model().objects.all()


@snitch.register(OTHER_DYNAMIC_SPAM)
class OtherDynamicSpamHandler(snitch.EventHandler):
    cool_down_manager_class = snitch.CoolDownManager
    cool_down_attempts = "method_dynamic_cool_down_attempts"
    cool_down_time = "method_dynamic_cool_down_time"
    notification_backends = [PushNotificationBackend]

    def audience(self):
        return get_user_model().objects.all()

    def method_dynamic_cool_down_attempts(self, receiver: models.Model):
        return 5

    def method_dynamic_cool_down_time(self, receiver: models.Model):
        return 5
