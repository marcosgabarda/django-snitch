from typing import TYPE_CHECKING, Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

from snitch.handlers import manager
from snitch.settings import NOTIFICATION_EAGER

if TYPE_CHECKING:
    from snitch import EventHandler
    from snitch.backends import AbstractBackend

User = get_user_model()


class EventType(models.Model):
    """Explicit model for Event types, represented by the event verb. It's used to
    enable or disable the generation of notifications.
    """

    verb = models.CharField(
        max_length=255, null=True, choices=manager.choices(), unique=True
    )
    enabled = models.BooleanField(default=True, verbose_name=_("enabled"))

    class Meta:
        verbose_name = _("event type")
        verbose_name_plural = _("event types")
        ordering = ("verb",)

    def __str__(self) -> str:
        return self.verb


class Event(TimeStampedModel):
    """A 'event' is generated when an 'actor' performs 'verb', involving 'action',
    in the 'target'.

     It could be:
        <actor> <verb>
        <actor> <verb> <target>
        <actor> <verb> <trigger> <target>

    Reference: http://activitystrea.ms/specs/atom/1.0/
    """

    actor_content_type = models.ForeignKey(
        ContentType,
        related_name="actor_actions",
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("actor content type"),
    )
    actor_object_id = models.PositiveIntegerField(_("actor object id"), null=True)
    actor = GenericForeignKey("actor_content_type", "actor_object_id")

    verb = models.CharField(
        _("verb"), max_length=255, null=True, choices=manager.choices()
    )

    trigger_content_type = models.ForeignKey(
        ContentType,
        related_name="trigger_actions",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("trigger content type"),
    )
    trigger_object_id = models.PositiveIntegerField(
        _("trigger object id"), blank=True, null=True
    )
    trigger = GenericForeignKey("trigger_content_type", "trigger_object_id")

    target_content_type = models.ForeignKey(
        ContentType,
        related_name="target_actions",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("target content type"),
    )
    target_object_id = models.PositiveIntegerField(
        _("target object id"), blank=True, null=True
    )
    target = GenericForeignKey("target_content_type", "target_object_id")

    notified = models.BooleanField(_("notified"), default=False)

    class Meta:
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self) -> str:
        handler = self.handler()
        return handler.get_text()

    def handler(self, notification: "Notification" = None) -> "EventHandler":
        """Gets the handler for the event."""
        return manager.handler(self, notification=notification)

    def notify(self) -> None:
        """Creates the notifications associated to this action, ."""
        handler = self.handler()
        if handler.should_notify:
            handler.notify()
            self.notified = True
            self.save()

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if not self.notified:
            self.notify()


class AbstractNotification(TimeStampedModel):
    """A notification is sent to an user, and it's always related with an event."""

    event = models.ForeignKey(
        Event,
        verbose_name=_("event"),
        related_name="notifications",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="notifications", on_delete=models.CASCADE
    )
    sent = models.BooleanField(_("sent"), default=False)
    received = models.BooleanField(_("received"), default=False)
    read = models.BooleanField(_("read"), default=False)

    class Meta:
        verbose_name = _("notification")
        verbose_name_plural = _("notifications")
        ordering = ("-created",)
        abstract = True

    def __str__(self) -> str:
        return f"'{str(self.event)}' to {str(self.user)}"

    def _task_kwargs(self, handler: "EventHandler") -> Dict:
        """Gets the kwargs for celery task, used in apply_async method."""
        kwargs = {}
        # Delay from event handler
        delay = handler.get_delay()
        if delay:
            kwargs["countdown"] = delay
        return kwargs

    def handler(self) -> "EventHandler":
        """Gets the handler for the notification."""
        return self.event.handler(notification=self)

    def send(self, send_async: bool = False) -> None:
        """Sends a push notification to the devices of the user."""
        from snitch.tasks import send_notification_task

        handler: "EventHandler" = self.event.handler()
        if handler.should_send:
            if send_async:
                send_notification_task.apply_async(
                    (self.pk,), **self._task_kwargs(handler)
                )
            else:
                # Activate language for translations
                if settings.USE_I18N:
                    language = handler.get_language(self.user)
                    translation.activate(language)
                for backend_class in handler.notification_backends:
                    backend: "AbstractBackend" = backend_class(self)
                    backend.send()
                self.sent = True
                self.save()

    def save(self, *args, **kwargs) -> None:
        """Overwrite to sending push notifications when saving."""
        is_insert: bool = self._state.adding
        super().save(*args, **kwargs)
        if is_insert:
            self.send(send_async=NOTIFICATION_EAGER)


class Notification(AbstractNotification):
    """Initial notification model that can be swappable."""

    class Meta(AbstractNotification.Meta):
        swappable: str = "SNITCH_NOTIFICATION_MODEL"
