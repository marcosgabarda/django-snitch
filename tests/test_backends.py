import pytest
from django.contrib.contenttypes.models import ContentType
from push_notifications.models import GCMDevice

from snitch.backends import PushNotificationBackend
from snitch.models import Event
from tests.app.events import CONFIRMED_EVENT, LOCALIZED_EVENT
from tests.app.factories import GCMDeviceFactory, StuffFactory
from tests.app.models import Notification
from tests.factories import UserFactory


@pytest.mark.django_db
class TestPushNotificationBackend:
    def test_build_gcm_message(self):
        users = UserFactory.create_batch(size=5)
        for user in users:
            GCMDeviceFactory(
                user=user,
            )
        stuff = StuffFactory()
        stuff.confirm()
        assert Event.objects.filter(verb=CONFIRMED_EVENT).count() == 1
        notification = Notification.objects.first()
        backend = PushNotificationBackend(notification)
        assert backend.get_devices(GCMDevice).count() == 1
        message, extra = backend._build_gcm_message(
            devices=backend.get_devices(GCMDevice)
        )
        assert message == "Stuff object (1) confirmed"
        content_type = ContentType.objects.get_for_model(stuff)
        assert extra == {
            "title": notification.handler().get_title(),
            "action_type": f"{content_type.app_label}.{content_type.model}",
            "action_id": stuff.pk,
            "notification": notification.pk,
        }

    def test_send_to_devices_batch(self):
        users = UserFactory.create_batch(size=5)
        for user in users:
            GCMDeviceFactory(
                user=user,
            )
        stuff = StuffFactory()
        stuff.confirm()
        assert Event.objects.filter(verb=CONFIRMED_EVENT).count() == 1
        notification = Notification.objects.first()
        backend = PushNotificationBackend(notification)
        assert backend.get_devices(GCMDevice).count() == 1
        backend.send()

    def test_send_to_devices_no_batch(self):
        users = UserFactory.create_batch(size=5)
        for user in users:
            GCMDeviceFactory(
                user=user,
            )
        stuff = StuffFactory()
        stuff.confirm()
        assert Event.objects.filter(verb=CONFIRMED_EVENT).count() == 1
        notification = Notification.objects.first()
        backend = PushNotificationBackend(notification)
        backend.batch_sending = False
        assert backend.get_devices(GCMDevice).count() == 1
        backend.send()

    def test_localized_event(self):
        user = UserFactory()
        GCMDeviceFactory(user=user)
        stuff = StuffFactory()
        stuff.localized()
        assert Event.objects.filter(verb=LOCALIZED_EVENT).count() == 1
        notification = Notification.objects.first()
        backend = PushNotificationBackend(notification)
        assert backend.get_devices(GCMDevice).count() == 1
        message, extra = backend._build_gcm_message(
            devices=backend.get_devices(GCMDevice)
        )
        assert message is None
        content_type = ContentType.objects.get_for_model(stuff)
        assert extra == {
            "action_type": f"{content_type.app_label}.{content_type.model}",
            "action_id": stuff.pk,
            "notification": notification.pk,
            "body_loc_args": [],
            "body_loc_key": "localized_text",
            "title_loc_args": [],
            "title_loc_key": "localized_title",
        }
