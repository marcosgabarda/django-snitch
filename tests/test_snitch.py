from django.test import TestCase

import snitch
from snitch.models import Event
from tests.app.events import (
    ACTIVATED_EVENT,
    ActivatedHandler,
    DUMMY_EVENT,
    DummyHandler,
    CONFIRMED_EVENT,
    ConfirmedHandler,
)
from tests.app.factories import (
    StuffFactory,
    ActorFactory,
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
        self.assertEqual(ActivatedHandler.title, event.title())

    def test_dispatch_event_with_backends(self):
        users = UserFactory.create_batch(size=5)
        self.assertEqual(0, Event.objects.filter(verb=CONFIRMED_EVENT).count())
        stuff = StuffFactory()
        stuff.confirm()
        self.assertEqual(1, Event.objects.filter(verb=CONFIRMED_EVENT).count())
        event = Event.objects.filter(verb=CONFIRMED_EVENT).first()
        self.assertTrue(isinstance(event.handler(), ConfirmedHandler))
        self.assertEqual(ConfirmedHandler.title, event.title())
        self.assertTrue(event.notified)
        self.assertEqual(len(users), Notification.objects.all().count())

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
