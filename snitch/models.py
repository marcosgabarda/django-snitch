from typing import Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from snitch import EventHandler
from snitch.handlers import manager

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

    def __str__(self):
        return str(self.verb)


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

    def __str__(self):
        return self.text()

    def handler(self):
        """Gets the handler for the event. Save the instance of the handler in the
        model.
        """
        if not hasattr(self, "_handler_instance"):
            self._handler_instance = manager.handler(self)
        return self._handler_instance

    def text(self):
        """Gets the human readable text for the event."""
        handler = self.handler()
        return handler.get_text()

    def title(self):
        """Gets the title for the event."""
        handler = self.handler()
        return handler.get_title()

    def action_type(self):
        """Gets the action type depending on the verb."""
        handler = self.handler()
        return handler.get_action_type()

    def action_id(self):
        """Gets the action id depending on the verb."""
        handler = self.handler()
        return handler.get_action_id()

    def notify(self):
        """Creates the notifications associated to this action, ."""
        handler = self.handler()
        if handler.should_notify:
            handler.notify()
            self.notified = True
            self.save()

    def save(self, *args, **kwargs):
        result = super().save(*args, **kwargs)
        if not self.notified:
            self.notify()
        return result


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

    def __str__(self):
        return "'{}' to {}".format(str(self.event), str(self.user))

    def _task_kwargs(self, handler: EventHandler) -> Dict:
        """Gets the kwargs for celery task, used in apply_async method."""
        kwargs = {}
        # Delay from event handler
        delay = handler.get_delay()
        if delay:
            kwargs["countdown"] = delay
        return kwargs

    def send(self, send_async: bool = False):
        """Sends a push notification to the devices of the user."""
        from .tasks import send_notification_task

        handler: EventHandler = self.event.handler()
        if handler.should_send:
            if send_async:
                send_notification_task.apply_async(
                    (self.pk,), **self._task_kwargs(handler)
                )
            else:
                for backend_class in handler.notification_backends:
                    backend = backend_class(self)
                    backend.send()
                self.sent = True
                self.save()

    def save(self, *args, **kwargs):
        """Overwrite to sending push notifications when saving."""
        is_insert = self._state.adding
        super().save(*args, **kwargs)
        if is_insert:
            self.send()


class Notification(AbstractNotification):
    """Initial notification model that can be swappable."""

    class Meta(AbstractNotification.Meta):
        swappable = "SNITCH_NOTIFICATION_MODEL"
