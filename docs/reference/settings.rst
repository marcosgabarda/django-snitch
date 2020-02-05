========
Settings
========

Here is a list of all available settings of ``django-snitch`` and their
default values. All settings are prefixed with ``SNITCH_``, although this
is a bit verbose it helps to make it easy to identify these settings.


SNITCH_NOTIFICATION_MODEL
    Default: ``"snitch.Notification"``

    Allows to swap de Notification model of an own version.

SNITCH_ENABLED_SEND_NOTIFICATIONS
    Default: ``True``

    Activate or deactivate the creation of notifications.

SNITCH_ENABLED_SEND_EMAILS
    Default: ``True``

    Activate or deactivate the email sending.