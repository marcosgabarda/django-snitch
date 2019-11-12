import logging
from typing import Dict, Union, Type, Optional

from django.contrib.auth import get_user_model
from push_notifications.gcm import GCMError
from push_notifications.models import GCMDevice, APNSDevice

from snitch.emails import TemplateEmailMessage
from snitch.settings import ENABLED_SEND_NOTIFICATIONS

logger = logging.getLogger(__name__)
User = get_user_model()


class AbstractBackend:
    """Abstract backend class for notifications."""

    def __init__(self, notification: "Notification"):
        self.notification: "Notification" = notification
        self.title: str = self.notification.event.title()
        self.text: str = self.notification.event.text()
        self.action_type: str = self.notification.event.action_type()
        self.action_id: str = self.notification.event.action_id()

    def send(self):
        """A subclass should to implement the send method."""
        raise NotImplementedError


class PushNotificationBackend(AbstractBackend):
    """A backend class to send push notifications depending on the platform."""

    def extra_data(self) -> Dict:
        """Gets the extra data to add to the push, to be hooked if needed."""
        return {}

    def _get_devices(
        self, device_class: Union[Type[GCMDevice], Type[APNSDevice]]
    ) -> "QuerySet":
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

    template_email_kwargs_attr: str = "template_email_kwargs"
    get_email_kwargs_attr: str = "get_email_kwargs_attr"
    get_email_extra_context_attr: str = "get_email_extra_context"
    get_email_subject_attr: str = "get_email_subject"

    def __use_async(self) -> bool:
        """Check if the email can use async."""
        handler = self.notification.event.handler()
        return (
            handler.template_email_async
            if hasattr(handler, "template_email_async")
            else True
        )

    def extra_context(self) -> Dict:
        """Gets extra context to the email if there is a method in the handler."""
        handler = self.notification.event.handler()
        if hasattr(handler, self.get_email_extra_context_attr):
            return getattr(handler, self.get_email_extra_context_attr)()
        return {}

    def subject(self) -> Optional[str]:
        """Gets subject of the email if there is a method in the handler."""
        handler = self.notification.event.handler()
        if hasattr(handler, self.get_email_subject_attr):
            return getattr(handler, self.get_email_subject_attr)()
        return None

    def email_kwargs(self) -> Optional[dict]:
        """Dynamically gets the kwargs for TemplateEmailMessage"""
        handler = self.notification.event.handler()
        kwargs = None
        if hasattr(handler, self.get_email_kwargs_attr):
            kwargs = getattr(handler, self.get_email_kwargs_attr)()
        elif hasattr(handler, self.template_email_kwargs_attr):
            kwargs = getattr(handler, self.template_email_kwargs_attr)
        return kwargs

    def send(self):
        """Sends the email."""
        if ENABLED_SEND_NOTIFICATIONS:
            # Gets the handler to extract the arguments from template_email_kwargs
            handler = self.notification.event.handler()
            kwargs = self.email_kwargs()
            if kwargs:
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
                # Override subject
                subject = self.subject()
                if subject:
                    kwargs["subject"] = subject
                # Context
                context = kwargs.get("context", {})
                context.update({"notification": self.notification})
                context.update(self.extra_context())
                kwargs.update({"context": context})
                # Sends email
                email = TemplateEmailMessage(**kwargs)
                email.send(use_async=self.__use_async())
