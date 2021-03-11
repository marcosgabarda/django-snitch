from django.conf import settings

# Needed to build and publish with Flit
# ------------------------------------------------------------------------------
SECRET_KEY = "snitch"

# Specific project configuration
# ------------------------------------------------------------------------------
NOTIFICATION_EAGER = getattr(settings, "SNITCH_NOTIFICATION_EAGER", False)
ENABLED_SEND_NOTIFICATIONS = getattr(
    settings, "SNITCH_ENABLED_SEND_NOTIFICATIONS", True
)
ENABLED_SEND_EMAILS = getattr(settings, "SNITCH_ENABLED_SEND_EMAILS", True)
NOTIFICATION_MODEL = getattr(
    settings, "SNITCH_NOTIFICATION_MODEL", "snitch.Notification"
)
