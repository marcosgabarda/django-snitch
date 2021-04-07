from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SnitchConfig(AppConfig):
    """The default AppConfig for admin which does automatic discovery."""

    name: str = "snitch"
    verbose_name: str = _("Snitch")

    def ready(self):
        super().ready()
        self.module.autodiscover()
