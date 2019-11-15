.. :changelog:

History
-------

1.4.0 (2019-11-15)
+++++++++++++++++

* Added ``schedules`` app.

1.3.1 (2019-11-12)
+++++++++++++++++

* Added ``get_email_kwargs_attr`` function to handler to dynamical set the values of kwargs for email.
* Can't use async when there is an attachment.

1.3.0 (2019-10-18)
+++++++++++++++++

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
+++++++++++++++++

* First release on PyPI.
