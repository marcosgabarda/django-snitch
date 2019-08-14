from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SimpleSnitchConfig(AppConfig):
    """Simple AppConfig which does not do automatic discovery."""

    name = "snitch"
    verbose_name = _("Snitch")


class SnitchConfig(SimpleSnitchConfig):
    """The default AppConfig for admin which does automatic discovery."""

    def ready(self):
        super().ready()
        self.module.autodiscover()
