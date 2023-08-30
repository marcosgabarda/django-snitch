"""Django app made to integrate generic events that create notifications that
can be sent to users using several backends.

By default, it integrates push notifications and email to send the
notifications.
"""
from pathlib import Path

import django
from django.utils.module_loading import autodiscover_modules
from single_source import get_version

from snitch.cooldowns import CoolDownManager
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
    "CoolDownManager",
]
__version__ = get_version(__name__, Path(__file__).parent.parent) or "1.0.0"
__version_info__ = tuple(
    [
        int(num) if num.isdigit() else num
        for num in __version__.replace("-", ".", 1).split(".")
    ]
)


def autodiscover():
    autodiscover_modules("events", register_to=manager)


if django.VERSION < (3, 2):
    default_app_config = "snitch.apps.SnitchConfig"
