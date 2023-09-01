from typing import TYPE_CHECKING, Tuple, Type

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from snitch.exceptions import HandlerError
from snitch.helpers import (
    extract_actor_trigger_target,
    get_notification_model,
    send_event_to_user,
)
from snitch.tasks import create_notification_task

if TYPE_CHECKING:  # pragma: no cover
    from django.contrib.auth.models import AbstractBaseUser

    from snitch.backends import AbstractBackend
    from snitch.cooldowns import AbstractCoolDownManager
    from snitch.models import Event, Notification


class EventHandler:
    """Base event backend to generic even types."""

    # Generic
    ephemeral: bool = False
    dispatch_config: dict = {"args": ("actor", "trigger", "target")}
    title: str | None = None
    text: str | None = None
    delay: int = 0
    notification_creation_async: bool = False
    notification_backends: list[Type["AbstractBackend"]] = []

    # Cool down
    cool_down_manager_class: Type["AbstractCoolDownManager"] | None = None

    # Email backend
    template_email_async: bool = False
    template_email_kwargs: dict = {}

    # Push notification backend
    action_attribute: str = "actor"
    action_type: str | None = None
    action_id: str | None = None
    click_action: str | None = None
    use_localization_keys: bool = False

    @classmethod
    def extract_actor_trigger_target(cls, method: str, *args, **kwargs):
        """Extracts actor, trigger and target from the args and kwargs
        given as parameters. Override to implement a specific extractor.
        """
        if not isinstance(cls.dispatch_config, dict) or (
            "args" not in cls.dispatch_config and "kwargs" not in cls.dispatch_config
        ):
            raise HandlerError(_("The dispatch config is incorrect."))
        return extract_actor_trigger_target(
            config=cls.dispatch_config, args=args, kwargs=kwargs
        )

    def __init__(self, event: "Event", notification: "Notification | None" = None):
        self.event = event
        self.notification = notification
        self.cool_down_manager = (
            self.cool_down_manager_class(event_handler=self)
            if self.cool_down_manager_class
            else None
        )

    def __str__(self) -> str:
        return (
            self.get_text() or self.get_text_localization_key()
            if self.use_localization_keys
            else "-"
        )

    def _default_dynamic_text(self) -> str:
        """Makes an event human readable."""
        text = "{} {}".format(str(self.event.actor), self.event.verb)
        if self.event.trigger:
            text = "{} {}".format(text, str(self.event.trigger))
        if self.event.target:
            text = "{} {}".format(text, str(self.event.target))
        return text

    def should_notify(self, receiver: "models.Model") -> bool:
        """Used by the event to create or not the notifications to the audience. If the
        notification is not created, there isn't any notification sent
        (push, email, etc), and there isn't any record in the database."""
        if self.cool_down_manager:
            return self.cool_down_manager.should_notify(receiver=receiver)
        return True

    def should_send(self, receiver: "models.Model") -> bool:
        """Used by the notification to send or not the notification to the user. If
        returns False, the notification is created in the database but not sent.
        """
        if self.cool_down_manager:
            return self.cool_down_manager.should_send(receiver=receiver)
        return True

    def get_text(
        self, receivers: "models.QuerySet | models.Model | None" = None
    ) -> str | None:
        """Override to handle different human readable implementations."""
        if self.use_localization_keys:
            return None
        return self.text or self._default_dynamic_text()

    def get_title(
        self, receivers: "models.QuerySet | models.Model | None" = None
    ) -> str | None:
        """Gets the title for the event. To be hooked."""
        if self.use_localization_keys:
            return None
        return self.title

    def get_title_localization_key(
        self, receivers: "models.QuerySet | models.Model | None"
    ) -> str:
        """Use by default the verb as localization key, replacing spaces and adding
        the suffix '_title'."""
        return f'{self.event.verb.replace(" ", "_")}_title'

    def get_title_localization_args(
        self, receivers: "models.QuerySet | models.Model | None"
    ) -> list:
        """By default, no arguments for localization."""
        return []

    def get_text_localization_key(
        self, receivers: "models.QuerySet | models.Model | None" = None
    ) -> str:
        """Use by default the verb as localization key, replacing spaces and adding
        the suffix '_texts'."""
        return f'{self.event.verb.replace(" ", "_")}_text'

    def get_text_localization_args(
        self, receivers: "models.QuerySet | models.Model | None" = None
    ) -> list:
        """By default, no arguments for localization."""
        return []

    def get_action_type(self) -> str | None:
        """Gets the action type depending on the verb. The actor by default, since
        is the only mandatory field.
        """
        try:
            ContentType = apps.get_model("contenttypes.ContentType")
            action = getattr(self.event, self.action_attribute)
            content_type = ContentType.objects.get_for_model(action)
            return f"{content_type.app_label}.{content_type.model}"
        except AttributeError:
            return None

    def get_action_id(self) -> str | None:
        """Gets the action ID depending on the verb. The actor by default, since
        is the only mandatory field.
        """
        try:
            action = getattr(self.event, self.action_attribute)
            return action.pk
        except AttributeError:
            return None

    def get_click_action(self) -> str | None:
        """Gets the click action depending on the verb. To be hooked."""
        return self.click_action

    def get_delay(self) -> int:
        """Returns and in, number of seconds, that corresponds with the time
        the notification should be delayed.
        """
        return self.delay

    def get_language(self, user: "AbstractBaseUser | None") -> str:
        """Gets the locale for the given used. By default, users the LANGUAGE_CODE
        value from settings.
        """
        return settings.LANGUAGE_CODE

    def get_extra_data(
        self, receivers: "models.QuerySet | models.Model | None" = None
    ) -> dict:
        """Adds extra meta data to the backend."""
        return {}

    def audience(self) -> "QuerySet":
        """Gets the audience of the event. None by default, to be hooked by the user."""
        User = get_user_model()
        return User.objects.none()

    def notify(self):
        """If the event is not ephemeral, creates a notification fot each user in the
        audience. In other case, only sends the notification, but doesn't save
        into the database.
        """
        if not self.ephemeral:
            # Creates a notification
            ContentType = apps.get_model("contenttypes.ContentType")
            Notification = get_notification_model()
            for receiver in self.audience().iterator():
                if self.should_notify(receiver=receiver):
                    if self.notification_creation_async:
                        create_notification_task.delay(
                            self.event.pk,
                            receiver.id,
                            ContentType.objects.get_for_model(receiver).pk,
                        )
                    else:
                        notification = Notification(event=self.event, receiver=receiver)
                        notification.save()
        else:
            # Only sends the event to the user
            for user in self.audience().iterator():
                send_event_to_user(event=self.event, user=user)

    def after_send(self, receiver: "models.Model") -> None:
        """Executes logic after the notification is sent fot the given receiver."""
        if self.cool_down_manager:
            return self.cool_down_manager.after_send(receiver=receiver)

    def after_notify(self, receiver: "models.Model") -> None:
        """Executes logic after the notification is sent fot the given receiver."""
        if self.cool_down_manager:
            return self.cool_down_manager.after_notify(receiver=receiver)


class EventManager:
    """The event manager in the responsible of handling the registration of the
    handlers with the verbs.
    """

    _registry: dict[str, Type["EventHandler"]]
    _verbs: dict

    def __init__(self):
        self._registry = {}
        self._verbs = {}

    def register(
        self, verb: str, handler: Type["EventHandler"], verbose: str | None = None
    ):
        """Register a handler with a verb, and the verbose form of the verb."""
        if not issubclass(handler, EventHandler):
            raise HandlerError(
                _(f"The handler {handler} have to inherit from EventHandler.")
            )
        self._verbs[verb] = verbose if verbose else verb
        self._registry[verb] = handler

    def choices(self) -> Tuple:
        """Gets a tuple of tuples with the registers verbs and its verbose form, to be
        used as choices."""
        return tuple(self._verbs.items())

    def handler_class(self, verb) -> Type[EventHandler]:
        """Returns a class instance of the handler for the given verb."""
        return self._registry.get(verb, EventHandler)

    def handler(
        self, event: "Event", notification: "Notification | None" = None
    ) -> EventHandler:
        """Returns an instance of the handler for the given event."""
        return self.handler_class(event.verb)(event, notification=notification)


# This global object represents the singleton event manager object
manager: EventManager = EventManager()
