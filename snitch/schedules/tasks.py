from django.db.models import F

from celery.task import task


@task(serializer="json")
def execute_schedule_task(schedule_id):
    from snitch.schedules.models import Schedule

    try:
        schedule = Schedule.objects.get(pk=schedule_id)
    except (Schedule.DoesNotExist, ValueError):
        return None
    schedule.run()
    return schedule_id


@task(serializer="json")
def clean_scheduled_tasks():
    """Task to clean one shot periodic tasks. Note that this can be done better
     using the proper attributes for PeriodicTask.
     """
    from snitch.schedules.models import Schedule

    schedules = Schedule.objects.filter(limit__isnull=False).filter(
        counter__gte=F("limit")
    )
    # Delete one by one to be sure all the signals and logic beyond delete method
    # are executed
    for schedule in schedules.iterator():
        schedule.delete()
