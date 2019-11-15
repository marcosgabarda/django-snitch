import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import DAYS

from snitch.schedules.models import Schedule
from tests.app.events import DUMMY_EVENT, EVERY_HOUR
from tests.app.models import OtherStuff


@receiver(post_save, sender=OtherStuff)
def post_save_other_stuff(sender, instance, created, **kwargs):
    """Creates the schedules for other stuff."""
    if created:
        # sent a dummy event in 2 days
        schedule = Schedule(
            actor=instance,
            verb=DUMMY_EVENT,
            limit=1,
            every=2,
            period=DAYS,
            start_time=instance.created + datetime.timedelta(days=2),
        )
        schedule.save()
        # sent a dummy event evert hour, but with cron
        schedule = Schedule(
            actor=instance, verb=EVERY_HOUR, minute=instance.created.minute, hour="*/1"
        )
        schedule.save()
