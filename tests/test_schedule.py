import warnings

import pytest
from django_celery_beat.models import DAYS

from snitch.models import Event
from snitch.schedules.models import Schedule
from snitch.schedules.tasks import clean_scheduled_tasks, execute_schedule_task
from tests.app.events import DUMMY_EVENT, EVERY_HOUR
from tests.app.factories import OtherStuffFactory


@pytest.mark.django_db
class TestSnitchSchedule:
    def test_create_other_stuff(self):
        assert Schedule.objects.all().count() == 0
        OtherStuffFactory()
        assert Schedule.objects.filter(verb=DUMMY_EVENT).count() == 1
        assert Schedule.objects.filter(verb=DUMMY_EVENT).exists()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        assert schedule.period == DAYS
        assert schedule.every == 2
        assert schedule.limit == 1

    def test_create_other_stuff_every_hour(self):
        assert Schedule.objects.all().count() == 0
        other_stuff = OtherStuffFactory()
        assert Schedule.objects.filter(verb=EVERY_HOUR).count() == 1
        assert Schedule.objects.filter(verb=EVERY_HOUR).exists()
        schedule = Schedule.objects.filter(verb=EVERY_HOUR).first()
        assert schedule.minute == str(other_stuff.created.minute)
        assert schedule.hour == "*/1"

    def test_execute_schedule_task(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        assert schedule.counter == 0
        schedule_pk = execute_schedule_task(schedule.pk)
        assert schedule.pk == schedule_pk
        schedule.refresh_from_db()
        assert schedule.counter == 1

    def test_execute_schedule_task_not_found(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        assert schedule.counter == 0
        schedule_pk = execute_schedule_task(0)
        assert schedule_pk is None
        schedule.refresh_from_db()
        assert schedule.counter == 0

    def test_clean_scheduled_tasks(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        execute_schedule_task(schedule.pk)
        clean_scheduled_tasks()
        assert Schedule.objects.filter(verb=DUMMY_EVENT).count() == 0

    def test_scheduled_task_without_actor(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        schedule.actor = None
        schedule.save()
        with warnings.catch_warnings(record=True) as warns:
            warnings.simplefilter("always")
            schedule.run()
            assert len(warns) == 1
            assert UserWarning == warns[-1].category
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 0

    def test_clean_scheduled_tasks_run(self):
        OtherStuffFactory()
        schedule = Schedule.objects.filter(verb=DUMMY_EVENT).first()
        schedule.run()
        assert Event.objects.filter(verb=DUMMY_EVENT).count() == 1
