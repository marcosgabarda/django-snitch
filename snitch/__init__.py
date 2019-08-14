from django.utils.module_loading import autodiscover_modules

from snitch.decorators import register, dispatch
from snitch.handlers import manager, EventHandler
from snitch.helpers import explicit_dispatch, get_notification_model
from snitch.settings import NOTIFICATION_MODEL


__all__ = [
    "register",
    "manager",
    "EventHandler",
    "dispatch",
    "explicit_dispatch",
    "get_notification_model",
]

__version__ = "0.1"


def autodiscover():
    autodiscover_modules("events", register_to=manager)


default_app_config = "snitch.apps.SnitchConfig"
