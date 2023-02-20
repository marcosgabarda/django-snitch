import io

from django.contrib.auth import get_user_model

import snitch
from snitch.backends import EmailNotificationBackend, PushNotificationBackend

ACTIVATED_EVENT = "activated"
CONFIRMED_EVENT = "confirmed"
DUMMY_EVENT = "dummy"
EVERY_HOUR = "every hour"
SMALL_EVENT = "small"
DUMMY_EVENT_NO_BODY = "dummy no body"
SPAM = "spam"


@snitch.register(ACTIVATED_EVENT)
class ActivatedHandler(snitch.EventHandler):
    title = "Activated!"

    notification_backends = [PushNotificationBackend, EmailNotificationBackend]

    # Custom configuration for email backend
    template_email_kwargs = {"template_name": "email.html"}
    template_email_async = False


@snitch.register(CONFIRMED_EVENT)
class ConfirmedHandler(snitch.EventHandler):
    title = "Confirmed!"
    notification_backends = [PushNotificationBackend, EmailNotificationBackend]

    # Custom configuration for email backend
    template_email_kwargs = {"template_name": "email.html"}
    template_email_async = False

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
    template_email_async = False


@snitch.register(DUMMY_EVENT_NO_BODY)
class DummyNoBodyHandler(snitch.EventHandler):
    def get_title(self) -> str | None:
        return None

    def get_text(self) -> str | None:
        return None


@snitch.register(SPAM)
class SpamHandler(snitch.EventHandler):
    cool_down_attempts = 5
    cool_down_time = 5
    notification_backends = [PushNotificationBackend]

    def audience(self):
        return get_user_model().objects.all()
