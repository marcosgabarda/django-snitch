================
Cool Down System
================

Django-snitch implements a cool down system, so a user can set a limit of how many 
notification will be sent to a user in a time period.

.. code-block:: python

    import snitch

    SPAM = "spam"


    @snitch.register(SPAM)
    class SpamHandler(snitch.EventHandler):
    
        cool_down_manager_class = snitch.CoolDownManager
        cool_down_attempts = 5
        cool_down_time = 5  # In seconds
        notification_backends = [PushNotificationBackend]

It uses `Django’s cache framework <https://docs.djangoproject.com/en/4.0/topics/cache/#the-low-level-cache-api>`_ 
to handle the count of how many notifications are sent to a user. You can configure 


``cool_down_manager_class``
    Default: ``None```

    Indicates the class that should be used to handle the cool down. It is set to 
    ``None`` by default, and you should specify the class to use this function. 
    Django-snitch comes with the class ``snitch.CoolDownManager`` that can be used.

``cool_down_attempts``
    Default: ``1``

    It handles the number of notifications that have to be sent in order to stop the sending. This 
    can be an int, a callable that returns an integer number or a string and receives two arguments, 
    and ``snitch.EventHandler`` and a ``receiver`` as a Django Model. If it's a string,
    it should reference a method in the handler with and argument, the ``receiver`` .
    
``cool_down_time``
    Default: ``0``

    It handles the number of seconds to wait until the notifications will be send again. This 
    can be an int, a callable that returns an integer number or a string and receives two arguments, 
    and ``snitch.EventHandler`` and a ``receiver`` as a Django Model. If it's a string,
    it should reference a method in the handler with and argument, the ``receiver`` .

``cool_down_cache_alias``
    Default: ``default``

    This property is used by ``snitch.CoolDownManager`` and allows to use a different 
    alias for the cache.

The cache key is created using the event verb and the receiver data, app label, model name and primary key.

.. code-block:: python

    class CoolDownManager(AbstractCoolDownManager):

        def _key(self, receiver: "models.Model", suffix: str = "") -> str:
            """Get the cache key used by the cool down manager."""
            if receiver.pk is None:
                raise AttributeError("The receiver should have a primary key.")
            key = f"[{self.prefix}]cool-down-{self.event_handler.event.verb}-{receiver._meta.app_label}-{receiver._meta.model_name}-{receiver.pk}"
            if suffix:
                key = f"{key}-{suffix}"
            return key

Therefore, the counter by default is unique for each receiver and each event verb.

Cool Down Manager
-----------------

In the ``EventHandler`` it can be specified a different ``CoolDownManager`` class by 
changing the attribute ``cool_down_manager_class`` in the  ``EventHandler``.

.. code-block:: python

    import snitch
    from snitch.cooldowns import AbstractCoolDownManager

    SPAM = "spam"


    class CustomCoolDownManager(AbstractCoolDownManager):
        
        def should_notify(self, receiver: "models.Model") -> bool:
            """By default, always notify."""
            return True

        def should_send(self, receiver: "models.Model") -> bool:
            """By default, always send."""
            return True


    @snitch.register(SPAM)
    class SpamHandler(snitch.EventHandler):
        cool_down_attempts = 5
        cool_down_time = 5 
        cool_down_manager_class = CustomCoolDownManager
        notification_backends = [PushNotificationBackend]