from django.contrib.auth import get_user_model

import snitch
from snitch.backends import PushNotificationBackend, EmailNotificationBackend

ACTIVATED_EVENT = "activated"
CONFIRMED_EVENT = "confirmed"
DUMMY_EVENT = "dummy"


@snitch.register(ACTIVATED_EVENT)
class ActivatedHandler(snitch.EventHandler):
    title = "Activated!"


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


@snitch.register(DUMMY_EVENT)
class DummyHandler(snitch.EventHandler):
    title = "Dummy event"
