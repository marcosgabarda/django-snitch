===================
Events and Handlers
===================

Events
------

An 'event' is generated when an 'actor' performs 'verb', involving 'action',
in the 'target'.

It could be

.. code-block::

    <actor> <verb>
    <actor> <verb> <target>
    <actor> <verb> <trigger> <target>

If is inspired in the `Atom Activity Streams <http://activitystrea.ms/specs/atom/1.0/>`_.

Event Handler Configuration
---------------------------

The base ``EventHandler`` class has the following definition:

.. code-block:: python

    class EventHandler:

        # Generic
        ephemeral: bool = False
        dispatch_config: dict = {"args": ("actor", "trigger", "target")}
        title: str | None = None
        text: str | None = None
        delay: int = 0
        notification_creation_async: bool = False
        notification_backends: list[Type["AbstractBackend"]] = []
        
        # Cool down
        cool_down_manager_class: Type["AbstractCoolDownManager"] | None = None

        # Email backend
        template_email_async: bool = False
        template_email_kwargs: dict = {}

        # Push notification backend
        action_attribute: str = "actor"
        action_type: str | None = None
        action_id: str | None = None
        click_action: str | None = None

Attributes
^^^^^^^^^^

Each attribute is used to handle the behavior of the event once is dispatched.

``ephemeral``
    Default: ``False``

    If this class variable is set to ``True``, the notification object will no be 
    created in the database.

``dispatch_config``
    Default: ``{"args": ("actor", "trigger", "target")}``

    This dictionary is used to extract the actor, trigger and target from the arguments 
    of the function that dispatch the event.

``title``
    Default: ``None``

    If defined, it will be the default title string of the notification.

``text``
    Default: ``None``

    If defined, it will be the default text body of the notification.

``delay``
    Default: ``0``

    De value of the attribute ``countdown`` in the launch of the task that 
    launches the notification.

``notification_creation_async```
    Default: ``False``

    If it's set to ``True``, then a Celery task is used to create the notification 
    model.

``notification_backends```
    Default: ``[]``

    List of notification backends that the handler should use in order to send the 
    notification to the audience. 

``cool_down_manager_class``
    Default: ``None``

    Indicates the class that should be used to handle the cool down. You should specify 
    the class to use this function. 
    
    Django-snitch comes with the class ``snitch.CoolDownManager`` that can be used.
    It uses `Django’s cache framework <https://docs.djangoproject.com/en/4.0/topics/cache/#the-low-level-cache-api>`_ 
    to handle the count of how many notifications are sent to a user.

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


``template_email_async``
    Default: ``False``
    
    Sets if the email can use async, ``False`` by default, because the notification
    is already sent using a task.

``template_email_kwargs``
    Default: ``{}``

    The kwargs values fot the TemplateEmailMessage used to send and email.

``action_attribute``
    Default: ``actor``

    Attribute of the event used to set the action attribute in the push 
    notification.

``action_type``
    Default: ``None``

    The string to identify the class o type of the action attribute in the push 
    notification.

``action_id``
    Default: ``None``

    The string to identify the specific action to be send in the push notification.

``click_action```
    Default: ``None``

    The string used by the clients that receives the push notification.

``use_localization_keys``
    Default: ``False``

    If set to ``True``, the notifications will be sent using the ``get_title_localization_key``method and 
    ``get_text_localization_key`` method.


Methods to overwrite
^^^^^^^^^^^^^^^^^^^^

.. py:function:: should_notify(self, receiver: "models.Model")

    Used by the event to create or not the notifications to the audience. If the
    notification is not created, there isn't any notification sent
    (push, email, etc), and there isn't any record in the database.

   :param receiver: The receiver object of the notification.
   :type receiver: models.Model
   :return: If the notification should be created.
   :rtype: bool

.. py:function:: should_send(self, receiver: "models.Model")

    Used by the notification to send or not the notification to the user. If
    returns False, the notification is created in the database but not sent.

   :param receiver: The receiver object of the notification.
   :type receiver: models.Model
   :return: If the notification should be sent.
   :rtype: bool

.. py:function:: get_text(self)

    Override to handle different human readable implementations of the notification 
    text.

   :return: The text of the notification.
   :rtype: str


.. py:function:: get_title(self)

    Override to handle different human readable implementations of the notification 
    title.

   :return: The title of the notification.
   :rtype: str

.. py:function:: audience(self)

    Gets the audience of the event. None by default, to be hooked by the user.

   :return: The QuerySet of the receivers of the notification.
   :rtype: models.QuerySet
