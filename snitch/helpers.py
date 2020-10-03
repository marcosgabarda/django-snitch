from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import translation

from snitch.constants import DEFAULT_CONFIG
from snitch.settings import NOTIFICATION_MODEL

if TYPE_CHECKING:
    from snitch.handlers import EventHandler
    from snitch.models import Event


def get_notification_model():
    """Return the Notification model that is active in this project."""
    try:
        return django_apps.get_model(NOTIFICATION_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "NOTIFICATION_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "NOTIFICATION_MODEL refers to model '%s' that has not been installed"
            % NOTIFICATION_MODEL
        )


def explicit_dispatch(
    verb: str, config: Optional[Dict] = DEFAULT_CONFIG, *args, **kwargs
) -> Any:
    """Helper to explicit dispatch an event without using a decorator."""
    from snitch.decorators import dispatch

    return dispatch(verb=verb, method=False, config=config)(
        lambda *args, **kwargs: None
    )(*args, **kwargs)


def extract_actor_trigger_target(config: Dict, args: Tuple, kwargs: Dict) -> Tuple:
    """Extracts the actor, trigger and target using the arguments config given from
    the generic arguments args and kwargs.
    """
    actor = trigger = target = None
    if "args" in config:
        arguments_args = config.get("args", tuple())
        try:
            actor = args[arguments_args.index("actor")]
        except (ValueError, IndexError):
            pass
        try:
            trigger = args[arguments_args.index("trigger")]
        except (ValueError, IndexError):
            pass
        try:
            target = args[arguments_args.index("target")]
        except (ValueError, IndexError):
            pass
    if "kwargs" in config:
        arguments_kwargs = config.get("kwargs", dict())
        try:
            actor = kwargs[arguments_kwargs.get("actor")]
        except (ValueError, KeyError):
            pass
        try:
            trigger = kwargs[arguments_kwargs.get("trigger")]
        except (ValueError, KeyError):
            pass
        try:
            target = kwargs[arguments_kwargs.get("target")]
        except (ValueError, KeyError):
            pass
    return actor, trigger, target


def send_event_to_user(event: "Event", user) -> None:
    """Takes the event and sends it to the user using the backend of the event
    handler.
    """
    handler: "EventHandler" = event.handler()
    if handler.should_send:
        # Activate language for translations
        if settings.USE_I18N:
            language = handler.get_language(user)
            translation.activate(language)
        for backend_class in handler.notification_backends:
            backend = backend_class(event=event, user=user)
            backend.send()
