DEBUG = True
USE_TZ = True

SECRET_KEY = "dummy"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "snitch",
    "tests.app",
]

# Schedules
INSTALLED_APPS += ["django_celery_beat", "snitch.schedules"]

SITE_ID = 1
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English")]
MIDDLEWARE = ()
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "debug": DEBUG,
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]

# DJANGO PUSH NOTIFICATIONS
# ------------------------------------------------------------------------------
# See: https://github.com/jazzband/django-push-notifications
INSTALLED_APPS += ("push_notifications",)
PUSH_NOTIFICATIONS_SETTINGS = {
    "CONFIG": "push_notifications.conf.AppConfig",
    "APPLICATIONS": {"snitch": {"PLATFORM": "FCM", "API_KEY": ""}},
}

# SNITCH SETTINGS
# ------------------------------------------------------------------------------
SNITCH_NOTIFICATION_MODEL = "app.Notification"
SNITCH_ENABLED_SEND_EMAILS = False
