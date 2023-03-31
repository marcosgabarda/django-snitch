import time
import warnings
from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.test import TestCase
from django_celery_beat.models import DAYS

import snitch
from snitch.models import Event
from snitch.schedules.models import Schedule
from snitch.schedules.tasks import clean_scheduled_tasks, execute_schedule_task
from tests.app.emails import WelcomeEmail, WelcomeHTMLEmail
from tests.app.events import (
    ACTIVATED_EVENT,
    CONFIRMED_EVENT,
    DUMMY_EVENT,
    DUMMY_EVENT_NO_BODY,
    DYNAMIC_SPAM,
    EVERY_HOUR,
    OTHER_DYNAMIC_SPAM,
    SMALL_EVENT,
    SPAM,
    ActivatedHandler,
    ConfirmedHandler,
    DummyHandler,
    SpamHandler,
)
from tests.app.factories import (
    ActorFactory,
    OtherStuffFactory,
    StuffFactory,
    TargetFactory,
    TriggerFactory,
)
from tests.app.helpers import dispatch_dummy_event, dispatch_explicit_dummy_event
from tests.app.models import Notification
from tests.factories import UserFactory


class SnitchTestCase(TestCase):
    def test_swappable_notification_model(self):
        notification_model_class = snitch.get_notification_model()
        self.assertTrue(issubclass(notification_model_class, Notification))

    def test_register_event(self):
        # This test assume that there is an events.py file in the testing app
        self.assertIn(ACTIVATED_EVENT, snitch.manager._verbs)
        self.assertIn(ACTIVATED_EVENT, snitch.manager._registry)
        self.assertTrue(
            issubclass(snitch.manager._registry[ACTIVATED_EVENT], snitch.EventHandler)
        )

    def test_dispatch_event(self):
        self.assertEqual(0, Event.objects.filter(verb=ACTIVATED_EVENT).count())
        stuff = StuffFactory()
        stuff.activate()
        self.assertEqual(1, Event.objects.filter(verb=ACTIVATED_EVENT).count())
        event = Event.objects.filter(verb=ACTIVATED_EVENT).first()
        self.assertTrue(isinstance(event.handler(), ActivatedHandler))
        handler = event.handler()
        self.assertEqual(ActivatedHandler.title, handler.get_title())

    def test_dispatch_event_with_backends(self):
        users = UserFactory.create_batch(size=5)
        self.assertEqual(0, Event.objects.filter(verb=CONFIRMED_EVENT).count())
        stuff = StuffFactory()
        stuff.confirm()
        self.assertEqual(1, Event.objects.filter(verb=CONFIRMED_EVENT).count())
        event = Event.objects.filter(verb=CONFIRMED_EVENT).first()
        self.assertTrue(isinstance(event.handler(), ConfirmedHandler))
        handler = event.handler()
        self.assertEqual(ConfirmedHandler.title, handler.get_title())
        self.assertTrue(event.notified)
        self.assertEqual(len(users), Notification.objects.all().count())
        notification_handler = Notification.objects.first().handler()
        self.assertIsNotNone(notification_handler.notification)

    def test_dispatch_event_from_function(self):
        self.assertEqual(0, Event.objects.filter(verb=DUMMY_EVENT).count())
        dispatch_dummy_event(
            actor=ActorFactory(), target=TargetFactory(), trigger=TriggerFactory()
        )
        self.assertEqual(1, Event.objects.filter(verb=DUMMY_EVENT).count())
        event = Event.objects.filter(verb=DUMMY_EVENT).first()
        self.assertTrue(isinstance(event.handler(), DummyHandler))
        self.assertIsNotNone(event.target)
        self.assertIsNotNone(event.trigger)

    def test_dispatch_event_from_function_explicit(self):
        self.assertEqual(0, Event.objects.filter(verb=DUMMY_EVENT).count())
        dispatch_explicit_dummy_event(
            actor=ActorFactory(), target=TargetFactory(), trigger=TriggerFactory()
        )
        self.assertEqual(1, Event.objects.filter(verb=DUMMY_EVENT).count())
        event = Event.objects.filter(verb=DUMMY_EVENT).first()
        self.assertTrue(isinstance(event.handler(), DummyHandler))
        self.assertIsNotNone(event.target)
        self.assertIsNotNone(event.trigger)

    def test_dispatch_event_from_function_bad_attributes(self):
        self.assertEqual(0, Event.objects.filter(verb=DUMMY_EVENT).count())
        dispatch_dummy_event(ActorFactory(), TargetFactory(), TriggerFactory())
        self.assertEqual(0, Event.objects.filter(verb=DUMMY_EVENT).count())

    def test_create_other_stuff(self):
        schedules = Schedule.objects.all().count()
        self.assertEqual(0, schedules)
        OtherStuffFactory()
        self.assertEqual(1, Schedule.objects.filter(verb=DUMMY_EVENT).count())
        self.assertTrue(Schedule.objects.filter(verb=DUMMY_EVENT).exists())
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        self.assertEqual(DAYS, schedule.period)
        self.assertEqual(2, schedule.every)
        self.assertEqual(1, schedule.limit)

    def test_create_other_stuff_every_hour(self):
        schedules = Schedule.objects.all().count()
        self.assertEqual(0, schedules)
        other_stuff = OtherStuffFactory()
        self.assertEqual(1, Schedule.objects.filter(verb=EVERY_HOUR).count())
        self.assertTrue(Schedule.objects.filter(verb=EVERY_HOUR).exists())
        schedule = Schedule.objects.filter(verb=EVERY_HOUR).first()
        self.assertEqual(str(other_stuff.created.minute), schedule.minute)
        self.assertEqual("*/1", schedule.hour)

    def test_execute_schedule_task(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        self.assertEqual(0, schedule.counter)
        schedule_pk = execute_schedule_task(schedule.pk)
        self.assertEqual(schedule_pk, schedule.pk)
        schedule.refresh_from_db()
        self.assertEqual(1, schedule.counter)

    def test_execute_schedule_task_not_found(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        self.assertEqual(0, schedule.counter)
        schedule_pk = execute_schedule_task(0)
        self.assertIsNone(schedule_pk)
        schedule.refresh_from_db()
        self.assertEqual(0, schedule.counter)

    def test_clean_scheduled_tasks(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        execute_schedule_task(schedule.pk)
        clean_scheduled_tasks()
        self.assertEqual(0, Schedule.objects.filter(verb=DUMMY_EVENT).count())

    def test_scheduled_task_without_actor(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        schedule.actor = None
        schedule.save()
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            schedule.run()
            self.assertEqual(1, len(warns))
            self.assertEqual(warns[-1].category, UserWarning)
        self.assertEqual(0, Event.objects.filter(verb=DUMMY_EVENT).count())

    def test_clean_scheduled_tasks_run(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        schedule.run()
        self.assertEqual(1, Event.objects.filter(verb=DUMMY_EVENT).count())

    def test_ephemeral_event(self):
        self.assertEqual(0, Event.objects.filter(verb=SMALL_EVENT).count())
        stuff = StuffFactory()
        stuff.small()
        self.assertEqual(1, Event.objects.filter(verb=SMALL_EVENT).count())
        self.assertEqual(
            0, Notification.objects.filter(event__verb=SMALL_EVENT).count()
        )

    def test_send_email(self):
        email = WelcomeEmail(to="test@example.com", context={})
        self.assertEqual(email.template_name, email.default_template_name)
        self.assertEqual(email.subject, email.default_subject)
        self.assertEqual(email.from_email, email.default_from_email)
        self.assertEqual(email.bcc, [])
        self.assertEqual(email.cc, [])
        self.assertEqual(email.attaches, [])
        self.assertEqual(email.default_context, {})
        email.send(use_async=False)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_with_cc_and_bcc(self):
        email = WelcomeEmail(
            to="test@example.com",
            cc=["test@test.com"],
            bcc=["test@tost.com"],
            context={},
        )
        email.send(use_async=False)
        self.assertEqual(email.cc, ["test@test.com"])
        self.assertEqual(email.bcc, ["test@tost.com"])
        self.assertIsNone(email.reply_to)
        self.assertEqual(len(mail.outbox), 1)

    def test_send_email_with_non_list_addresses(self):
        email = WelcomeEmail(
            to="test@example.com",
            cc="test@test.com",
            bcc="test@tost.com",
            context={},
        )
        email.send(use_async=False)
        self.assertEqual(email.cc, ["test@test.com"])
        self.assertEqual(email.bcc, ["test@tost.com"])
        self.assertIsNone(email.reply_to)
        self.assertEqual(len(mail.outbox), 1)

    @mock.patch("snitch.emails.ENABLED_SEND_EMAILS", False)
    def test_not_send_email_when_disabled(self):
        email = WelcomeEmail(to="test@example.com", context={})
        email.send(use_async=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_dispatch_event_without_title(self):
        self.assertEqual(0, Event.objects.filter(verb=DUMMY_EVENT_NO_BODY).count())
        stuff = StuffFactory()
        stuff.dummy()
        self.assertEqual(1, Event.objects.filter(verb=DUMMY_EVENT_NO_BODY).count())
        event = Event.objects.filter(verb=DUMMY_EVENT_NO_BODY).first()
        self.assertEqual("-", str(event))

    def test_plain_text_email(self):
        email = WelcomeHTMLEmail(
            to="test@example.com", cc="test@test.com", bcc="test@tost.com", context={}
        )
        self.assertEqual("Hello world!", email.get_plain_message())

    def test_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        for _ in range(SpamHandler.cool_down_attempts - 1):
            stuff.spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts - 1,
            Notification.objects.filter(
                event__verb=SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
        stuff.spam(user=user)
        stuff.spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts,
            Notification.objects.filter(
                event__verb=SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
        time.sleep(SpamHandler.cool_down_time + 1)
        stuff.spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts + 1,
            Notification.objects.filter(
                event__verb=SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )

    def test_function_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        for _ in range(SpamHandler.cool_down_attempts - 1):
            stuff.dynamic_spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts - 1,
            Notification.objects.filter(
                event__verb=DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
        stuff.dynamic_spam(user=user)
        stuff.dynamic_spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts,
            Notification.objects.filter(
                event__verb=DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
        time.sleep(SpamHandler.cool_down_time + 1)
        stuff.dynamic_spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts + 1,
            Notification.objects.filter(
                event__verb=DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )

    def test_method_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        for _ in range(SpamHandler.cool_down_attempts - 1):
            stuff.other_dynamic_spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts - 1,
            Notification.objects.filter(
                event__verb=OTHER_DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
        stuff.other_dynamic_spam(user=user)
        stuff.other_dynamic_spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts,
            Notification.objects.filter(
                event__verb=OTHER_DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
        time.sleep(SpamHandler.cool_down_time + 1)
        stuff.other_dynamic_spam(user=user)
        self.assertEqual(
            SpamHandler.cool_down_attempts + 1,
            Notification.objects.filter(
                event__verb=OTHER_DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count(),
        )
