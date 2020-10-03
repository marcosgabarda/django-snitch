from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SnitchSchedulesAppConfig(AppConfig):

    name: str = "snitch.schedules"
    verbose_name: str = _("Schedules")
