import snitch
from snitch import explicit_dispatch
from snitch.constants import DEFAULT_CONFIG
from tests.app.events import DUMMY_EVENT, DUMMY_EVENT_ASYNC


@snitch.dispatch(DUMMY_EVENT, config=DEFAULT_CONFIG)
def dispatch_dummy_event(actor, trigger, target):
    pass


@snitch.dispatch(DUMMY_EVENT_ASYNC, config=DEFAULT_CONFIG)
def dispatch_dummy_event_async(actor, trigger, target):
    pass


def dispatch_explicit_dummy_event(actor, trigger, target):
    explicit_dispatch(verb=DUMMY_EVENT, actor=actor, trigger=trigger, target=target)
