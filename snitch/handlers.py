from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from snitch.exceptions import HandlerError
from snitch.helpers import extract_actor_trigger_target, get_notification_model


class EventHandler:
    """Base event backend to generic even types."""

    should_notify = True
    should_send = True
    dispatch_config = {"args": ("actor", "trigger", "target")}
    action_type = None
    action_id = None
    title = None
    text = None
    notification_backends = []

    @classmethod
    def extract_actor_trigger_target(cls, method, *args, **kwargs):
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

    def __init__(self, event):
        self.event = event

    def _default_dynamic_text(self):
        """Makes an event human readable."""
        text = "{} {}".format(str(self.event.actor), self.event.verb)
        if self.event.trigger:
            text = "{} {}".format(text, str(self.event.trigger))
        if self.event.target:
            text = "{} {}".format(text, str(self.event.target))
        return text

    def get_text(self):
        """Override to handle different human readable implementations."""
        return self.text or self._default_dynamic_text()

    def get_title(self):
        """Gets the title for the event. To be hooked."""
        return self.title

    def get_action_type(self):
        """Gets the action type depending on the verb. To be hooked."""
        return self.action_type

    def get_action_id(self):
        """Gets the action depending on the verb. To be hooked."""
        return self.action_id

    def audience(self):
        """Gets the audience of the event. None by default, to be hooked by the user."""
        User = get_user_model()
        return User.objects.none()

    def notify(self):
        """Creates a notification fot each user in the audience."""
        Notification = get_notification_model()
        for user in self.audience():
            notification = Notification(event=self.event, user=user)
            notification.save()


class EventManager:
    """The event manager in the responsible of handling the registration of the
    handlers with the verbs.
    """

    def __init__(self):
        self._registry = {}
        self._verbs = {}

    def register(self, verb, handler, verbose=None):
        """Register a handler with a verb, and the verbose form of the verb."""
        if not issubclass(handler, EventHandler):
            raise HandlerError(
                _(f"The handler {handler} have to inherit from EventHandler.")
            )
        self._verbs[verb] = verbose if verbose else verb
        self._registry[verb] = handler

    def choices(self):
        """Gets a tuple of tuples with the registers verbs and its verbose form, to be
        used as choices."""
        return tuple(self._verbs.items())

    def handler_class(self, verb):
        """Returns a class instance of the handler for the given verb."""
        return self._registry.get(verb)

    def handler(self, event):
        """Returns an instance of the handler for the given event."""
        return self.handler_class(event.verb)(event)


# This global object represents the singleton event manager object
manager = EventManager()
