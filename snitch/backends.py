import logging
from typing import Dict, Optional, Type, Union

from django.contrib.auth import get_user_model

from snitch.emails import TemplateEmailMessage
from snitch.settings import ENABLED_SEND_NOTIFICATIONS

logger = logging.getLogger(__name__)
User = get_user_model()


class AbstractBackend:
    """Abstract backend class for notifications."""

    def __init__(
        self,
        notification: Optional["Notification"] = None,
        event: Optional["Event"] = None,
        user: Optional[User] = None,
    ):
        assert notification is not None or (
            event is not None and user is not None
        ), "You should provide a notification or an event and an user."

        self.notification: Optional["Notification"] = notification
        self.event: Optional["Event"] = event
        self.user: Optional[User] = user
        if self.notification:
            self.handler: "EventHandler" = self.notification.handler()
            self.user = self.notification.user
        elif self.event:
            self.handler: "EventHandler" = self.event.handler()

    def send(self):
        """A subclass should to implement the send method."""
        raise NotImplementedError


class PushNotificationBackend(AbstractBackend):
    """A backend class to send push notifications depending on the platform."""

    def __init__(self, *args, **kwargs):
        """Adds attributes for the push notification from the handler."""
        super().__init__(*args, **kwargs)
        self.title: str = self.handler.get_title()
        self.text: str = self.handler.get_text()
        self.action_type: str = self.handler.get_action_type()
        self.action_id: str = self.handler.get_action_id()

    def extra_data(self) -> Dict:
        """Gets the extra data to add to the push, to be hooked if needed."""
        return {}

    def _get_devices(
        self, device_class: Union[Type["GCMDevice"], Type["APNSDevice"]]
    ) -> "QuerySet":
        """Gets the devices using the given class."""
        return device_class.objects.filter(user=self.user)

    def _send_gcm(self):
        # While push_notifications is not working with Django 3.0, we are ignoring
        # the push sending
        try:
            from push_notifications.gcm import GCMError
            from push_notifications.models import GCMDevice
        except ImportError:
            return

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
        # While push_notifications is not working with Django 3.0, we are ignoring
        # the push sending
        try:
            from push_notifications.models import APNSDevice
            from push_notifications.apns import APNSError
        except ImportError:
            return

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
        except APNSError:
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
        """Check if the email can use async, False by default, because the notification
        is already sent using a task."""
        return (
            self.handler.template_email_async
            if hasattr(self.handler, "template_email_async")
            else False
        )

    def extra_context(self) -> Dict:
        """Gets extra context to the email if there is a method in the handler."""
        if hasattr(self.handler, self.get_email_extra_context_attr):
            return getattr(self.handler, self.get_email_extra_context_attr)()
        return {}

    def subject(self) -> Optional[str]:
        """Gets subject of the email if there is a method in the handler."""
        if hasattr(self.handler, self.get_email_subject_attr):
            return getattr(self.handler, self.get_email_subject_attr)()
        return None

    def email_kwargs(self) -> Optional[dict]:
        """Dynamically gets the kwargs for TemplateEmailMessage"""
        kwargs = None
        if hasattr(self.handler, self.get_email_kwargs_attr):
            kwargs = getattr(self.handler, self.get_email_kwargs_attr)()
        elif hasattr(self.handler, self.template_email_kwargs_attr):
            kwargs = getattr(self.handler, self.template_email_kwargs_attr)
        return kwargs

    def send(self):
        """Sends the email."""
        if ENABLED_SEND_NOTIFICATIONS:
            # Gets the handler to extract the arguments from template_email_kwargs
            kwargs = self.email_kwargs()
            if kwargs:
                # Gets to email
                email = (
                    getattr(User, "EMAIL_FIELD")
                    if hasattr(User, "EMAIL_FIELD")
                    else None
                )
                if email:
                    email_field_name = getattr(self.user, "EMAIL_FIELD")
                    kwargs.update({"to": getattr(self.user, email_field_name)})
                # Override subject
                subject = self.subject()
                if subject:
                    kwargs["subject"] = subject
                # Context
                context = kwargs.get("context", {})
                # Adds notification or event
                if self.notification:
                    context.update({"notification": self.notification})
                if self.event:
                    context.update({"event": self.event})
                context.update(self.extra_context())
                kwargs.update({"context": context})
                # Sends email
                email = TemplateEmailMessage(**kwargs)
                email.send(use_async=self.__use_async())
