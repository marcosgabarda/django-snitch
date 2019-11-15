from django.apps import AppConfig


class TestAppConfig(AppConfig):
    """Testing app."""

    name = "tests.app"

    def ready(self):
        try:
            import tests.app.signals
        except ImportError:
            pass
