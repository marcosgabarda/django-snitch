import logging
from typing import TYPE_CHECKING, Callable, Dict, Optional, Tuple, Type, Union

from django.contrib.auth import get_user_model
from django.db import models

from snitch.emails import TemplateEmailMessage
from snitch.settings import ENABLED_SEND_NOTIFICATIONS

if TYPE_CHECKING:
    from push_notifications.models import APNSDevice, GCMDevice

    from snitch.handlers import EventHandler
    from snitch.models import Event, Notification

logger = logging.getLogger(__name__)
User = get_user_model()

if TYPE_CHECKING:
    from django.contrib.auth.models import User as AuthUser
    from django.db import models
    from push_notifications.models import APNSDevice, GCMDevice

    from snitch.handlers import EventHandler
    from snitch.models import Event, Notification


class AbstractBackend:
    """Abstract backend class for notifications."""

    def __init__(
        self,
        notification: Optional["Notification"] = None,
        event: Optional["Event"] = None,
        user: Optional["AuthUser"] = None,
    ):
        assert notification is not None or (
            event is not None and user is not None
        ), "You should provide a notification or an event and an user."

        self.notification: Optional["Notification"] = notification
        self.event: Optional["Event"] = event
        self.user: Optional["AuthUser"] = user
        if self.notification:
            self.handler: "EventHandler" = self.notification.handler()
            self.user = self.notification.user
        elif self.event:
            self.handler = self.event.handler()

    def send(self):
        """A subclass should to implement the send method."""
        raise NotImplementedError


class PushNotificationBackend(AbstractBackend):
    """A backend class to send push notifications depending on the platform."""

    default_batch_sending: bool = True

    def __init__(self, *args, **kwargs):
        """Adds attributes for the push notification from the handler."""
        super().__init__(*args, **kwargs)
        self.action_type: str = self.handler.get_action_type()
        self.action_id: str = self.handler.get_action_id()
        self.batch_sending = kwargs.get("batch_sending", self.default_batch_sending)

    def extra_data(self) -> Dict:
        """Gets the extra data to add to the push, to be hooked if needed. It tries to
        get an initial dict from the handler.
        """
        return self.handler.get_extra_data()

    def get_devices(
        self, device_class: Union[Type["GCMDevice"], Type["APNSDevice"]]
    ) -> "models.QuerySet":
        """Gets the devices using the given class."""
        return device_class.objects.filter(user=self.user)

    def pre_send(
        self, device: Optional[Union["GCMDevice", "APNSDevice"]] = None
    ) -> None:
        """Actions previous to build the message and send, like activate translations if
        needed.
        """
        return None

    def post_send(
        self, device: Optional[Union["GCMDevice", "APNSDevice"]] = None
    ) -> None:
        """Actions post to sent the message, like deactivate translations if
        needed.
        """
        return None

    def _build_gcm_message(self) -> Tuple[str, Dict]:
        """Creates the message for GCM."""
        message: str = self.handler.get_text()
        extra = {}
        title: str = self.handler.get_title()
        if title:
            extra["title"] = title
        if self.action_type:
            extra["action_type"] = self.action_type
        if self.action_id:
            extra["action_id"] = self.action_id
        extra_data = self.extra_data()
        if extra_data:
            extra.update(extra_data)
        return message, extra

    def _build_apns_message(self) -> Tuple[Union[str, Dict], Dict]:
        """Creates the message for APNS."""
        text: str = self.handler.get_text()
        message: Union[str, Dict] = text
        extra: Dict = {}
        title: str = self.handler.get_title()
        if title:
            message = {"title": title, "body": text}
        if self.action_type:
            extra["action_type"] = self.action_type
        if self.action_id:
            extra["action_id"] = self.action_id
        extra_data = self.extra_data()
        if extra_data:
            extra.update(extra_data)
        return message, extra

    def _send_to_devices(self, devices: "models.QuerySet", building_method: Callable):
        """Sends a batch of pushes."""
        try:
            from push_notifications.apns import APNSError
            from push_notifications.gcm import GCMError
        except ImportError:
            return None
        if self.batch_sending:
            self.pre_send()
            message, extra = building_method()
            try:
                devices.send_message(message=message, extra=extra)
            except GCMError:
                logger.warning("Error sending a batch GCM push message")
            except APNSError:
                logger.warning("Error sending a batch APNS push message")
            self.post_send()
        else:
            for device in devices:
                self.pre_send(device=device)
                message, extra = building_method()
                try:
                    device.send_message(message=message, extra=extra)
                except GCMError:
                    logger.warning("Error sending a single GCM push message")
                except APNSError:
                    logger.warning("Error sending a single APNS push message")
                self.post_send(device=device)

        return None

    def _send_gcm(self):
        """Send to GCM devices."""
        try:
            from push_notifications.models import GCMDevice
        except ImportError:
            return None
        devices = self.get_devices(GCMDevice)
        self._send_to_devices(devices=devices, building_method=self._build_gcm_message)
        return None

    def _send_apns(self):
        """Send to APNS devices."""
        try:
            from push_notifications.models import APNSDevice
        except ImportError:
            return None
        devices = self.get_devices(APNSDevice)
        self._send_to_devices(devices=devices, building_method=self._build_apns_message)
        return None

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
            self.handler.template_email_async  # type: ignore
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
