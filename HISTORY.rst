.. :changelog:

History
-------

1.8.0 (2021-02-10)
++++++++++++++++++

* Fix: Replace ugettext by gettext.
* Fix: Cast email subject to str in send method.
* Feat: Better type checking.
* Feat: Added extra data method por EventHandler.
* Feat: Added system to handle individual sending or batch sending for pushes.

1.7.4 (2020-09-27)
++++++++++++++++++

* Added reply_to, bcc and cc to emails

1.7.3 (2020-08-31)
++++++++++++++++++

* Added use i18n parameter in emails

1.7.2 (2020-07-13)
++++++++++++++++++

* Fixed problem sending emails
* Changed to poetry as build tool

1.7.1 (2020-07-03)
++++++++++++++++++

* Fixed ephemeral events with push notifications
* Added default config to explicit_dispatch

1.7.0 (2020-06-25)
++++++++++++++++++

* Added ephemeral events

1.6.1 (2020-04-08)
++++++++++++++++++

* Fixed problem with handler instance cache


1.6.0 (2020-04-08)
++++++++++++++++++

* Added Notification object to the EventHandler, to be able to customize the handler methods depending on the notification user

1.5.0 (2019-12-12)
++++++++++++++++++

* Added support to Django 3.0
* Added translation activation for async notifications

1.4.1 (2019-11-18)
++++++++++++++++++

* Added admin for ``schedules``.

1.4.0 (2019-11-15)
++++++++++++++++++

* Added ``schedules`` app.

1.3.1 (2019-11-12)
++++++++++++++++++

* Added ``get_email_kwargs_attr`` function to handler to dynamical set the values of kwargs for email.
* Can't use async when there is an attachment.

1.3.0 (2019-10-18)
++++++++++++++++++

* Added delay for notifications.
* Starting to use type hints.

1.2.1 (2019-9-17)
+++++++++++++++++

* Fixed notification send task.

1.2.0 (2019-9-13)
+++++++++++++++++

* Added extra context and custom subject to email backend.

1.1.1 (2019-9-12)
+++++++++++++++++

* Added method to get the devices in the push backend.

1.1.0 (2019-9-12)
+++++++++++++++++

* Change the action info send in push notifications.

1.0.4 (2019-8-27)
+++++++++++++++++

* Changed admin module.

1.0.3 (2019-8-27)
+++++++++++++++++

* Fixed bug in ``push_task`` task.

1.0.2 (2019-8-26)
+++++++++++++++++

* Fixed bug in ``EmailNotificationBackend``.

1.0.1 (2019-8-14)
+++++++++++++++++

* Fixed bug in ``explicit_dispatch``.

1.0 (2019-8-14)
+++++++++++++++

* First release on PyPI.
