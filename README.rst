=============
Django Snitch
=============

Django app made to integrate generic events that create notifications that
can be sent to users using several backends.

By default, it integrates **push notifications** and **email** to send the
notifications.

Quick start
-----------

**1** Install using pip::

    $ pip install django-snitch

**2** Add "snitch" to your INSTALLED_APPS settings like this::

    INSTALLED_APPS += ('snitch',)

**3** Create an `events.py` file