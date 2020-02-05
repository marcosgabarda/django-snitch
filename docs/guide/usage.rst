===============
Getting Started
===============

Registering events handlers
---------------------------

Django-snitch uses a system similar to django admin to register event handlers with
events. For doing that, first you need to create an ``events.py`` file in your
Django app.

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


Dispatching events
------------------

Once you have registered all the events handlers you need, the next step is to dispatch
these events when an action is performed.

In order to do that, you can use the ``dispatch`` decorator:

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
