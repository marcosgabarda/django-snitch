import time

import pytest
from django.contrib.contenttypes.models import ContentType

from tests.app.events import (
    DYNAMIC_SPAM,
    NO_SPAM,
    OTHER_DYNAMIC_SPAM,
    SPAM,
    SpamHandler,
)
from tests.app.factories import StuffFactory
from tests.app.models import Notification
from tests.factories import UserFactory


@pytest.mark.django_db
class TestSnitchCoolDown:
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

    def test_zero_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        stuff.no_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=NO_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == 1
        )
        time.sleep(1)
        stuff.no_spam(user=user)
        stuff.no_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=NO_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == 3
        )

    def test_function_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        for _ in range(SpamHandler.cool_down_attempts - 1):
            stuff.dynamic_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts - 1
        )
        stuff.dynamic_spam(user=user)
        stuff.dynamic_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts
        )
        time.sleep(SpamHandler.cool_down_time + 1)
        stuff.dynamic_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts + 1
        )

    def test_method_cool_down(self):
        user = UserFactory()
        stuff = StuffFactory()
        for _ in range(SpamHandler.cool_down_attempts - 1):
            stuff.other_dynamic_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=OTHER_DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts - 1
        )
        stuff.other_dynamic_spam(user=user)
        stuff.other_dynamic_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=OTHER_DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts
        )
        time.sleep(SpamHandler.cool_down_time + 1)
        stuff.other_dynamic_spam(user=user)
        assert (
            Notification.objects.filter(
                event__verb=OTHER_DYNAMIC_SPAM,
                receiver_id=user.pk,
                receiver_content_type=ContentType.objects.get_for_model(user),
            ).count()
            == SpamHandler.cool_down_attempts + 1
        )
