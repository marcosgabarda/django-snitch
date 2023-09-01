import logging
from typing import TYPE_CHECKING, Callable, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as AuthUser
from django.db import models

from snitch.emails import TemplateEmailMessage
from snitch.settings import ENABLED_SEND_NOTIFICATIONS

if TYPE_CHECKING:  # pragma: no cover
    from push_notifications.models import APNSDevice, GCMDevice

    from snitch.handlers import EventHandler
    from snitch.models import AbstractNotification, Event


logger = logging.getLogger(__name__)
User = get_user_model()


class AbstractBackend:
    """Abstract backend class for notifications."""

    def __init__(
        self,
        notification: " AbstractNotification | None" = None,
        event: "Event | None" = None,
        user: AuthUser | None = None,
    ):
        assert notification is not None or (
            event is not None and user is not None
        ), "You should provide a notification or an event and an user."

        self.notification: "AbstractNotification | None" = notification
        self.event: "Event | None " = event
        self.user: AuthUser | None = user
        if self.notification:
            self.handler: EventHandler = self.notification.handler()
            self.user = self.notification.user
        elif self.event:
            self.handler = self.event.handler()

    def send(self):
        """A subclass should to implement the send method."""
        raise NotImplementedError


class PushNotificationBackend(AbstractBackend):
    """A backend class to send push notifications depending on the platform."""

    action_type: str | None
    action_id: str | None
    click_action: str | None
    default_batch_sending: bool = True
    batch_sending: bool

    def __init__(self, *args, **kwargs):
        """Adds attributes for the push notification from the handler."""
        super().__init__(*args, **kwargs)
        self.action_type = self.handler.get_action_type()
        self.action_id = self.handler.get_action_id()
        self.click_action = self.handler.get_click_action()
        self.batch_sending = kwargs.get("batch_sending", self.default_batch_sending)

    def extra_data(self, devices: "models.QuerySet | models.Model") -> dict:
        """Gets the extra data to add to the push, to be hooked if needed. It tries to
        get an initial dict from the handler.
        """
        extra_data = self.handler.get_extra_data(receivers=devices)
        # Add to the extra data the localization keys and args if use_localization_keys
        # is active
        if self.handler.use_localization_keys:
            extra_data["title_loc_key"] = self.handler.get_title_localization_key(
                receivers=devices
            )
            extra_data["title_loc_args"] = self.handler.get_title_localization_args(
                receivers=devices
            )
            extra_data["body_loc_key"] = self.handler.get_text_localization_key(
                receivers=devices
            )
            extra_data["body_loc_args"] = self.handler.get_text_localization_args(
                receivers=devices
            )
        return extra_data

    def get_devices(
        self,
        device_class: Type["GCMDevice"] | Type["APNSDevice"],
    ) -> "models.QuerySet":
        """Gets the devices using the given class."""
        if self.user is not None:
            return device_class.objects.filter(user=self.user)
        if self.notification and self.notification.receiver_class() == device_class:
            return device_class.objects.filter(pk=self.notification.receiver_id)
        return device_class.objects.none()

    def pre_send(
        self,
        device: "GCMDevice | APNSDevice | None" = None,
    ) -> None:
        """Actions previous to build the message and send, like activate translations if
        needed.
        """
        return None

    def post_send(
        self,
        device: "GCMDevice | APNSDevice | None" = None,
    ) -> None:
        """Actions post to sent the message, like deactivate translations if
        needed.
        """
        return None

    def _build_gcm_message(
        self, devices: "models.QuerySet | models.Model"
    ) -> tuple[str | None, dict]:
        """Creates the message for GCM."""
        message: str | None = self.handler.get_text(receivers=devices)
        extra = {}
        title: str | None = self.handler.get_title(receivers=devices)
        if title:
            extra["title"] = title
        if self.action_type:
            extra["action_type"] = self.action_type
        if self.action_id:
            extra["action_id"] = self.action_id
        if self.click_action:
            extra["click_action"] = self.click_action
        if self.notification:
            extra["notification"] = self.notification.pk
        extra_data = self.extra_data(devices=devices)
        if extra_data:
            extra.update(extra_data)
        return message, extra

    def _build_apns_message(
        self, devices: "models.QuerySet | models.Model"
    ) -> tuple[str | dict | None, dict]:
        """Creates the message for APNS."""
        text: str | None = self.handler.get_text(receivers=devices)
        message: str | dict | None = text
        extra: dict = {}
        title: str | None = self.handler.get_title(receivers=devices)
        if title:
            message = {"title": title, "body": text}
        if self.action_type:
            extra["action_type"] = self.action_type
        if self.action_id:
            extra["action_id"] = self.action_id
        if self.click_action:
            extra["click_action"] = self.click_action
        if self.notification:
            extra["notification"] = self.notification.pk
        extra_data = self.extra_data(devices=devices)
        if extra_data:
            extra.update(extra_data)
        return message, extra

    def _send_to_devices(
        self,
        devices: "models.QuerySet",
        message_builder: Callable[
            ["models.QuerySet | models.Model"], tuple[str | dict | None, dict]
        ],
    ):
        """Sends a batch of pushes."""
        if self.batch_sending:
            self.pre_send()
            try:
                message, extra = message_builder(devices)
                devices.send_message(message=message, extra=extra)
            except Exception as exception:
                logger.warning("Error sending a batch push message: %s", str(exception))
            self.post_send()
        else:
            for device in devices:
                self.pre_send(device=device)
                try:
                    message, extra = message_builder(device)
                    device.send_message(message=message, extra=extra)
                except Exception as exception:
                    logger.warning(
                        "Error sending a single push message: %s", str(exception)
                    )
                self.post_send(device=device)

        return None

    def _send_gcm(self) -> None:
        """Send to GCM devices."""
        try:
            from push_notifications.models import GCMDevice
        except ImportError:
            return None
        devices = self.get_devices(GCMDevice)
        self._send_to_devices(devices=devices, message_builder=self._build_gcm_message)
        return None

    def _send_apns(self) -> None:
        """Send to APNS devices."""
        try:
            from push_notifications.models import APNSDevice
        except ImportError:
            return None
        devices = self.get_devices(APNSDevice)
        self._send_to_devices(devices=devices, message_builder=self._build_apns_message)
        return None

    def send(self) -> None:
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

    def extra_context(self) -> dict:
        """Gets extra context to the email if there is a method in the handler."""
        if hasattr(self.handler, self.get_email_extra_context_attr):
            return getattr(self.handler, self.get_email_extra_context_attr)()
        return {}

    def subject(self) -> str | None:
        """Gets subject of the email if there is a method in the handler."""
        if hasattr(self.handler, self.get_email_subject_attr):
            return getattr(self.handler, self.get_email_subject_attr)()
        return None

    def email_kwargs(self) -> dict | None:
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
