import time
from unittest import mock

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core import mail

import snitch
from snitch.models import Event
from tests.app.emails import WelcomeEmail, WelcomeHTMLEmail
from tests.app.events import (
    ACTIVATED_EVENT,
    CONFIRMED_EVENT,
    DUMMY_EVENT,
    DUMMY_EVENT_ASYNC,
    DUMMY_EVENT_NO_BODY,
    SMALL_EVENT,
    SPAM,
    ActivatedHandler,
    ConfirmedHandler,
    DummyAsyncHandler,
    DummyHandler,
    SpamHandler,
)
from tests.app.factories import (
    ActorFactory,
    StuffFactory,
    TargetFactory,
    TriggerFactory,
)
from tests.app.helpers import (
    dispatch_dummy_event,
    dispatch_dummy_event_async,
    dispatch_explicit_dummy_event,
)
from tests.app.models import Notification
from tests.factories import UserFactory


@pytest.mark.django_db
class TestSnitch:
    def test_swappable_notification_model(self):
        notification_model_class = snitch.get_notification_model()
        assert issubclass(notification_model_class, Notification)

    def test_register_event(self):
        # This test assume that there is an events.py file in the testing app
        assert ACTIVATED_EVENT in snitch.manager._verbs
        assert ACTIVATED_EVENT in snitch.manager._registry
        assert issubclass(
            snitch.manager._registry[ACTIVATED_EVENT], snitch.EventHandler
        )

    def test_dispatch_event(self):
        assert Event.objects.filter(verb=ACTIVATED_EVENT).count() == 0
        stuff = StuffFactory()
        stuff.activate()
        assert Event.objects.filter(verb=ACTIVATED_EVENT).count() == 1
        event = Event.objects.filter(verb=ACTIVATED_EVENT).first()
        assert isinstance(event.handler(), ActivatedHandler)
        handler = event.handler()
        assert handler.get_title() == ActivatedHandler.title

    def test_dispatch_event_with_backends(self):
        users = UserFactory.create_batch(size=5)
        assert Event.objects.filter(verb=CONFIRMED_EVENT).count() == 0
        stuff = StuffFactory()
        stuff.confirm()
        assert Event.objects.filter(verb=CONFIRMED_EVENT).count() == 1
        event = Event.objects.filter(verb=CONFIRMED_EVENT).first()
        assert isinstance(event.handler(), ConfirmedHandler)
        handler = event.handler()
        assert handler.get_title() == ConfirmedHandler.title
        assert event.notified
        assert Notification.objects.all().count() == len(users)
        notification_handler = Notification.objects.first().handler()
        assert notification_handler.notification is not None

    def test_dispatch_event_with_backends_async(self):
        users = UserFactory.create_batch(size=5)
        assert Event.objects.filter(verb=DUMMY_EVENT_ASYNC).count() == 0
        dispatch_dummy_event_async(
            actor=ActorFactory(), target=TargetFactory(), trigger=TriggerFactory()
        )
        assert Event.objects.filter(verb=DUMMY_EVENT_ASYNC).count() == 1
        event = Event.objects.filter(verb=DUMMY_EVENT_ASYNC).first()
        assert isinstance(event.handler(), DummyAsyncHandler)
        assert Notification.objects.all().count() == len(users)
        notification_handler = Notification.objects.first().handler()
        assert notification_handler.notification is not None

    def test_dispatch_event_from_function(self):
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 0
        dispatch_dummy_event(
            actor=ActorFactory(), target=TargetFactory(), trigger=TriggerFactory()
        )
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 1
        event = Event.objects.filter(verb=DUMMY_EVENT).first()
        assert isinstance(event.handler(), DummyHandler)
        assert event.target is not None
        assert event.trigger

    def test_dispatch_event_from_function_explicit(self):
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 0
        dispatch_explicit_dummy_event(
            actor=ActorFactory(), target=TargetFactory(), trigger=TriggerFactory()
        )
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 1
        event = Event.objects.filter(verb=DUMMY_EVENT).first()
        assert isinstance(event.handler(), DummyHandler)
        assert event.target is not None
        assert event.trigger is not None

    def test_dispatch_event_from_function_bad_attributes(self):
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 0
        dispatch_dummy_event(ActorFactory(), TargetFactory(), TriggerFactory())
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 0

    def test_ephemeral_event(self):
        assert Event.objects.filter(verb=SMALL_EVENT).count() == 0
        stuff = StuffFactory()
        stuff.small()
        assert Event.objects.filter(verb=SMALL_EVENT).count() == 1
        assert Notification.objects.filter(event__verb=SMALL_EVENT).count() == 0

    def test_send_email(self):
        email = WelcomeEmail(to="test@example.com", context={})
        assert email.template_name == email.default_template_name
        assert email.subject == email.default_subject
        assert email.from_email == email.default_from_email
        assert email.bcc == []
        assert email.cc == []
        assert email.attaches == []
        assert email.default_context == {}
        email.send(use_async=False)
        assert 1 == len(mail.outbox)

    def test_send_email_with_cc_and_bcc(self):
        email = WelcomeEmail(
            to="test@example.com",
            cc=["test@test.com"],
            bcc=["test@tost.com"],
            context={},
        )
        email.send(use_async=False)
        assert email.cc == ["test@test.com"]
        assert email.bcc == ["test@tost.com"]
        assert email.reply_to is None
        assert len(mail.outbox) == 1

    def test_send_email_with_non_list_addresses(self):
        email = WelcomeEmail(
            to="test@example.com",
            cc="test@test.com",
            bcc="test@tost.com",
            context={},
        )
        email.send(use_async=False)
        assert ["test@test.com"] == email.cc
        assert ["test@tost.com"] == email.bcc
        assert email.reply_to is None
        assert len(mail.outbox) == 1

    @mock.patch("snitch.emails.ENABLED_SEND_EMAILS", False)
    def test_not_send_email_when_disabled(self):
        email = WelcomeEmail(to="test@example.com", context={})
        email.send(use_async=False)
        assert len(mail.outbox) == 0

    def test_dispatch_event_without_title(self):
        assert Event.objects.filter(verb=DUMMY_EVENT_NO_BODY).count() == 0
        stuff = StuffFactory()
        stuff.dummy()
        assert Event.objects.filter(verb=DUMMY_EVENT_NO_BODY).count() == 1
        event = Event.objects.filter(verb=DUMMY_EVENT_NO_BODY).first()
        assert str(event) == "-"

    def test_plain_text_email(self):
        email = WelcomeHTMLEmail(
            to="test@example.com", cc="test@test.com", bcc="test@tost.com", context={}
        )
        assert email.get_plain_message() == "Hello world!"

    def test_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        for _ in range(SpamHandler.cool_down_attempts - 1):
            stuff.spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts - 1
        )
        stuff.spam(user=user)
        stuff.spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts
        )
        time.sleep(SpamHandler.cool_down_time + 1)
        stuff.spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts + 1
        )
