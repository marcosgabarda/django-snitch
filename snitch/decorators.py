from typing import Callable, Dict, Optional

from snitch.helpers import extract_actor_trigger_target


def register(verb: str, verbose: Optional[str] = None) -> Callable:
    """Decorator to register an event with its handler.

    @events.register("verb", _("verb verbose"))
    class Handler(events.EventHandler):
        pass

    """
    from snitch.handlers import manager

    def _event_handler_wrapper(event_handler_class):
        manager.register(verb, event_handler_class, verbose=verbose)
        return event_handler_class

    return _event_handler_wrapper


def dispatch(
    verb: str, method: bool = False, config: Optional[Dict] = None
) -> Callable:
    """Decorator to dispatch an event when a method or function is called.

    The arguments attribute if to configure how to extract the actor, trigger and
    target from the decorated function arguments.

    config = {
        "args": ("actor", "trigger", "target")  # The position determines de type
        "kwargs": {"actor": "<name>", "trigger": "<name>", "target": "<name>"}
    }

    Example:

    @events.dispatch("verb")
    def method(self, trigger, target=None):
        # self is the actor
        pass

    """
    from django.contrib.contenttypes.models import ContentType

    from snitch.handlers import manager
    from snitch.models import Event, EventType

    def _decorator(func: Callable):
        """Decorator itself."""

        def _wrapper_trigger_action(*args, **kwargs):
            """Wrapped function with the decorator."""

            # Calls the function and saves the result
            result = func(*args, **kwargs)

            # Check if verb is enabled or not
            if EventType.objects.filter(verb=verb, enabled=False).exists():
                return result

            # Extract actor, trigger and target
            # If it isn't specified in arguments attribute, use the handler
            if config is None:
                handler_class = manager.handler_class(verb)
                actor, trigger, target = handler_class.extract_actor_trigger_target(
                    method, *args, **kwargs
                )
            # If it's explicit, use the arguments attribute
            else:
                if not isinstance(config, dict) or (
                    "args" not in config and "kwargs" not in config
                ):
                    return result
                actor, trigger, target = extract_actor_trigger_target(
                    config, args, kwargs
                )

            # Creates the event if there is an actor
            if actor:
                event = Event(
                    actor_content_type=ContentType.objects.get_for_model(actor),
                    actor_object_id=actor.pk,
                    verb=verb,
                )
                if trigger and hasattr(trigger, "pk") and trigger.pk is not None:
                    try:
                        event.trigger_content_type = ContentType.objects.get_for_model(
                            trigger
                        )
                        event.trigger_object_id = trigger.pk
                    except ContentType.DoesNotExist:
                        pass
                if target and hasattr(target, "pk") and target.pk is not None:
                    try:
                        event.target_content_type = ContentType.objects.get_for_model(
                            target
                        )
                        event.target_object_id = target.pk
                    except ContentType.DoesNotExist:
                        pass
                event.save()
            return result

        return _wrapper_trigger_action

    return _decorator
