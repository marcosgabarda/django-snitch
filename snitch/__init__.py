"""Django app made to integrate generic events that create notifications that
can be sent to users using several backends.

By default, it integrates push notifications and email to send the
notifications.
"""
import django
from django.utils.module_loading import autodiscover_modules

from snitch.decorators import dispatch, register
from snitch.handlers import EventHandler, manager
from snitch.helpers import explicit_dispatch, get_notification_model

__all__ = [
    "register",
    "manager",
    "EventHandler",
    "dispatch",
    "explicit_dispatch",
    "get_notification_model",
]

__version__ = "2.1.2"


def autodiscover():
    autodiscover_modules("events", register_to=manager)


if django.VERSION < (3, 2):
    default_app_config = "snitch.apps.SnitchConfig"
