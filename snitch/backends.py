import logging

from django.contrib.auth import get_user_model
from push_notifications.gcm import GCMError
from push_notifications.models import GCMDevice, APNSDevice

from snitch.emails import TemplateEmailMessage
from snitch.settings import ENABLED_SEND_NOTIFICATIONS

logger = logging.getLogger(__name__)
User = get_user_model()


class AbstractBackend:
    """Abstract backend class for notifications."""

    def __init__(self, notification):
        self.notification = notification
        self.title = self.notification.event.title()
        self.text = self.notification.event.text()
        self.action_type = self.notification.event.action_type()
        self.action_id = self.notification.event.action_id()

    def send(self):
        """A subclass should to implement the send method."""
        raise NotImplementedError


class PushNotificationBackend(AbstractBackend):
    """A backend class to send push notifications depending on the platform."""

    def extra_data(self):
        """Gets the extra data to add to the push, to be hooked if needed."""
        return {}

    def _get_devices(self, device_class):
        """Gets the devices using the given class."""
        return device_class.objects.filter(user=self.notification.user)

    def _send_gcm(self):
        devices = self._get_devices(GCMDevice)
        message = self.text
        extra = {}
        if self.title:
            extra["title"] = self.title
        if self.action_type:
            extra["action_type"] = self.action_type
        if self.action_id:
            extra["action_id"] = self.action_id
        if self.extra_data():
            extra.update(self.extra_data())
        try:
            devices.send_message(message=message, extra=extra)
        except GCMError:
            logger.warning("Error sending GCM push message")

    def _send_apns(self):
        devices = self._get_devices(APNSDevice)
        message = self.text
        extra = {}
        if self.title:
            message = {"title": self.title, "body": self.text}
        if self.action_type:
            extra["action_type"] = self.action_type
        if self.action_id:
            extra["action_id"] = self.action_id
        if self.extra_data():
            extra.update(self.extra_data())
        try:
            devices.send_message(message=message, extra=extra)
        except GCMError:
            logger.warning("Error sending APNS push message")

    def send(self):
        """Send message for each platform."""
        if ENABLED_SEND_NOTIFICATIONS:
            self._send_gcm()
            self._send_apns()


class EmailNotificationBackend(AbstractBackend):
    """Backend for using the email app to send emails."""

    def send(self):
        """Sends the email."""
        if ENABLED_SEND_NOTIFICATIONS:
            # Gets the handler to extract the arguments from template_email_kwargs
            handler = self.notification.event.handler()
            if hasattr(handler, "template_email_kwargs"):
                kwargs = handler.template_email_kwargs
                # Gets to email
                email = (
                    getattr(User, "EMAIL_FIELD")
                    if hasattr(User, "EMAIL_FIELD")
                    else None
                )
                if email:
                    email_field_name = getattr(self.notification.user, "EMAIL_FIELD")
                    kwargs.update(
                        {"to": getattr(self.notification.user, email_field_name)}
                    )
                # Context
                context = kwargs.get("context", {})
                context.update({"notification": self.notification})
                kwargs.update({"context": context})
                # Sends email
                email = TemplateEmailMessage(**kwargs)
                email.send(
                    use_async=handler.template_email_async
                    if hasattr(handler, "template_email_async")
                    else True
                )
