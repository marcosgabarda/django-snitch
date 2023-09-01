.. :changelog:

History
-------

3.2.0 (2023-08-31)
++++++++++++++++++

* Feat: Now the cool down manager is not set by default, you should define the manager class.
* Chore: Refactor in unit tests.

3.1.8 (2023-06-22)
++++++++++++++++++

* Fix: Fixed user to receiver migration.

3.1.7 (2023-03-31)
++++++++++++++++++

* Fix: TemplateEmailMessage bcc and cc parameters initiation #21.

3.1.1 (2023-02-24)
++++++++++++++++++

* Feat: Added missing pull request for async notifications.

3.1.0 (2023-02-23)
++++++++++++++++++

* Feat: Make the cool down manager optional.
* Feat: Added click action to payload and event handler.
* Feat: Added notification ID to payload.
* Feat: Added default behavior for action ID and action type.
* Feat: Updated cool down cache key to use a hash function.

3.0.1 (2023-02-22)
++++++++++++++++++

* Fix: Key compatible with Memcache.

3.0.0 (2023-02-22)
++++++++++++++++++

* BREAKING CHANGE: Removed ``user`` from notifications, and replaced with ``receiver`` to allow multiple types of audience.
* Feat: Added cool down system.
* Feat: Added option to create notifications using an async task.
* Chore: Updated to use Python 3.10 as minimum version.
* Chore: Updated type hints.
* Chore: Use single source to have the version in a single place.

2.3.0 (2023-02-02)
++++++++++++++++++

* Chore: Updated dependencies.
* Feat: IDs changed to BigAutoField.
* Feat: should_notify and should_send changed to property methods.
* Fix: Use of notification handler() method on send.

2.2.1 (2022-06-17)
++++++++++++++++++

* Fix: Version in package and updated dependencies.

2.2.0 (2022-06-17)
++++++++++++++++++

* Feat: Support for Django 4.0.
* Feat: Support for django-push-notifications 3.0.

2.1.1 (2021-09-15)
++++++++++++++++++

* Fix: Clean style tag for plain message.

2.0.2 (2021-06-19)
++++++++++++++++++

* Fix: Removed choices from event type verb to solve migrations when a verb is added.

2.0.1 (2021-06-10)
++++++++++++++++++

* Fix: Removed choices from event verb to solve migrations when a verb is added.

2.0.0 (2021-05-18)
++++++++++++++++++

* BREAKING CHANGE: migrate to `Celery 5 <https://docs.celeryproject.org/en/stable/whatsnew-5.0.html#upgrading-from-celery-4-x>`_
* Fix: eager condition.

1.8.3 (2021-03-11)
++++++++++++++++++

* Fix: notifications on save can be async or sync.

1.8.2 (2021-03-02)
++++++++++++++++++

* Fix: ensure "to", "reply_to", "cc" and "bcc" are valid email lists or None.

1.8.1 (2021-03-02)
++++++++++++++++++

* Fix: take into account cc, bcc and reply_to in async emails + fix typing.

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
