import os

from celery import Celery
from django.apps import AppConfig, apps
from django.conf import settings

if not settings.configured:
    # set the default Django settings module for the "celery" program.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "tests.settings"
    )  # pragma: no cover


app = Celery("tests")
app.config_from_object("django.conf:settings", namespace="CELERY")


class CeleryAppConfig(AppConfig):
    name = "tests.taskapp"
    verbose_name = "Celery Config"

    def ready(self):
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)
