from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Type

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from snitch.exceptions import HandlerError
from snitch.helpers import (
    extract_actor_trigger_target,
    get_notification_model,
    send_event_to_user,
)

if TYPE_CHECKING:
    from snitch.backends import AbstractBackend
    from snitch.models import Event, Notification


class EventHandler:
    """Base event backend to generic even types."""

    should_notify: bool = True
    should_send: bool = True
    ephemeral: bool = False
    dispatch_config: Dict = {"args": ("actor", "trigger", "target")}
    action_type: Optional[str] = None
    action_id: Optional[str] = None
    title: str = ""
    text: str = ""
    delay: int = 0
    notification_backends: List[Type["AbstractBackend"]] = []

    template_email_async: bool = False

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

    def __init__(self, event: "Event", notification: "Notification" = None):
        self.event = event
        self.notification = notification

    def _default_dynamic_text(self) -> str:
        """Makes an event human readable."""
        text = "{} {}".format(str(self.event.actor), self.event.verb)
        if self.event.trigger:
            text = "{} {}".format(text, str(self.event.trigger))
        if self.event.target:
            text = "{} {}".format(text, str(self.event.target))
        return text

    def get_text(self) -> str:
        """Override to handle different human readable implementations."""
        return self.text or self._default_dynamic_text()

    def get_title(self) -> str:
        """Gets the title for the event. To be hooked."""
        return self.title

    def get_action_type(self) -> Optional[str]:
        """Gets the action type depending on the verb. To be hooked."""
        return self.action_type

    def get_action_id(self) -> Optional[str]:
        """Gets the action depending on the verb. To be hooked."""
        return self.action_id

    def get_delay(self) -> int:
        """Returns and in, number of seconds, that corresponds with the time
        the notification should be delayed.
        """
        return self.delay

    def get_language(self, user=None) -> str:
        """Gets the locale for the given used. By default, users the LANGUAGE_CODE
        value from settings.
        """
        return settings.LANGUAGE_CODE

    def get_extra_data(self) -> Dict:
        """Adds extra meta data to the backend."""
        return {}

    def audience(self) -> QuerySet:
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
            Notification = get_notification_model()
            for user in self.audience():
                notification = Notification(event=self.event, user=user)
                notification.save()
        else:
            # Only sends the event to the user
            for user in self.audience():
                send_event_to_user(event=self.event, user=user)


class EventManager:
    """The event manager in the responsible of handling the registration of the
    handlers with the verbs.
    """

    def __init__(self):
        self._registry: Dict[str, Type["EventHandler"]] = {}
        self._verbs: Dict = {}

    def register(
        self, verb: str, handler: Type["EventHandler"], verbose: Optional[str] = None
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
        self, event: "Event", notification: "Notification" = None
    ) -> EventHandler:
        """Returns an instance of the handler for the given event."""
        return self.handler_class(event.verb)(event, notification=notification)


# This global object represents the singleton event manager object
manager: EventManager = EventManager()
