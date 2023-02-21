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
        cool_down_attempts = 5
        cool_down_time = 5  # In seconds
        notification_backends = [PushNotificationBackend]

It uses django cache system to handle the count of how many notifications are 
sent to a user.


Custom Cool Down Manager
------------------------

In the ``EventHandler`` it can be specified a different ``CoolDownManager`` class.