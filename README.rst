=============
Django Snitch
=============

.. image:: https://img.shields.io/pypi/v/django-snitch
    :target: https://pypi.org/project/django-snitch/
    :alt: PyPI

.. image:: https://codecov.io/gh/marcosgabarda/django-snitch/branch/main/graph/badge.svg?token=YKC608Q1HX 
    :target: https://codecov.io/gh/marcosgabarda/django-snitch

.. image:: https://img.shields.io/badge/code_style-black-000000.svg
    :target: https://github.com/ambv/black

.. image:: https://readthedocs.org/projects/django-snitch/badge/?version=latest
    :target: https://django-snitch.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Django app made to integrate generic events that create notifications that
can be sent to users using several backends.

By default, it integrates **push notifications** and **email** to send the
notifications.

Made with Python 3 and Django with :heart:.

Quick start
-----------

**1** Install using pip:

.. code-block:: bash

    pip install django-snitch

**2** Add "snitch" to your INSTALLED_APPS settings like this:

.. code-block:: python

    INSTALLED_APPS += ('snitch',)

**3** Create an ``events.py`` file in your app to register the events:

.. code-block:: python

    import snitch
    from snitch.backends import PushNotificationBackend, EmailNotificationBackend

    ACTIVATED_EVENT = "activated"
    CONFIRMED_EVENT = "confirmed"


    @snitch.register(ACTIVATED_EVENT)
    class ActivatedHandler(snitch.EventHandler):
        title = "Activated!"


    @snitch.register(CONFIRMED_EVENT)
    class ConfirmedHandler(snitch.EventHandler):
        title = "Confirmed!"
        notification_backends = [PushNotificationBackend, EmailNotificationBackend]

        # Custom configuration for email backend
        template_email_kwargs = {"template_name": "email.html"}
        template_email_async = False

        def audience(self):
            return get_user_model().objects.all()


**4** Use ``dispatch`` decorator to dispatch the event when a function is called:

.. code-block:: python

    from django.db import models
    from django.utils import timezone

    import snitch
    from snitch.models import AbstractNotification
    from tests.app.events import ACTIVATED_EVENT, CONFIRMED_EVENT


    class Stuff(models.Model):
        """Simple stuff model with status."""

        IDLE, ACTIVE, CONFIRMED = 0, 1, 2
        status = models.PositiveIntegerField(default=IDLE)
        activated_at = models.DateTimeField(null=True, blank=True)
        confirmed_at = models.DateTimeField(null=True, blank=True)

        @snitch.dispatch(ACTIVATED_EVENT)
        def activate(self):
            self.activated_at = timezone.now()

        @snitch.dispatch(CONFIRMED_EVENT)
        def confirm(self):
            self.confirmed_at = timezone.now()


Custom Notification model
-------------------------

You can, in the same way that ``django.contrib.auth.model.User`` works, swap the
Notification model, to customize it.

In order to do that, you should create a model that inherits from
``AbstractNotification``:

.. code-block:: python

    from django.db import models

    from snitch.models import AbstractNotification


    class Notification(AbstractNotification):
        """Custom notification."""

        extra_field = models.BooleanField(default=False)


And after that, specify it in the settings:

.. code-block:: python

    SNITCH_NOTIFICATION_MODEL = "app.Notification"
