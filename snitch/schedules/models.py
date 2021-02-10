import warnings

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

import snitch.handlers
from snitch.exceptions import SnitchError

try:
    from django_celery_beat.models import (
        PERIOD_CHOICES,
        CrontabSchedule,
        IntervalSchedule,
        PeriodicTask,
    )
except ImportError:
    raise SnitchError(
        "The snitch.schedules app requires the django-celery-beat package."
    )


class Schedule(TimeStampedModel):
    """A schedule event."""

    # Event data
    actor_content_type = models.ForeignKey(
        ContentType,
        related_name="actor_schedules",
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("actor content type"),
    )
    actor_object_id = models.PositiveIntegerField(_("actor object id"), null=True)
    actor = GenericForeignKey("actor_content_type", "actor_object_id")

    verb = models.CharField(
        _("verb"), max_length=255, null=True, choices=snitch.manager.choices()
    )

    trigger_content_type = models.ForeignKey(
        ContentType,
        related_name="trigger_schedules",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("trigger content type"),
    )
    trigger_object_id = models.PositiveIntegerField(
        _("trigger object id"), blank=True, null=True
    )
    trigger = GenericForeignKey("trigger_content_type", "trigger_object_id")

    target_content_type = models.ForeignKey(
        ContentType,
        related_name="target_schedules",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("target content type"),
    )
    target_object_id = models.PositiveIntegerField(
        _("target object id"), blank=True, null=True
    )
    target = GenericForeignKey("target_content_type", "target_object_id")

    # Repeat conditions
    limit = models.PositiveIntegerField(
        _("limit"), null=True, help_text="Set to null to always launch the event."
    )
    counter = models.PositiveIntegerField(
        _("counter"),
        default=0,
        help_text=_("Number of times the schedule has been executed."),
        blank=True,
    )

    # Interval values
    every = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Number of Periods"),
        help_text=_(
            "Number of interval periods to wait before " "running the task again"
        ),
        validators=[MinValueValidator(1)],
    )
    period = models.CharField(
        null=True,
        blank=True,
        max_length=24,
        choices=PERIOD_CHOICES,
        verbose_name=_("Interval Period"),
        help_text=_("The type of period between task runs (Example: days)"),
    )

    # Cron values
    minute = models.CharField(_("minute"), max_length=64, default="*")
    hour = models.CharField(_("hour"), max_length=64, default="*")
    day_of_week = models.CharField(_("day of week"), max_length=64, default="*")
    day_of_month = models.CharField(_("day of month"), max_length=64, default="*")
    month_of_year = models.CharField(_("month of year"), max_length=64, default="*")

    # Start datetime
    start_time = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Start Datetime"),
        help_text=_(
            "Datetime when the schedule should begin " "triggering the task to run"
        ),
    )

    # Periodic task
    task = models.ForeignKey(
        "django_celery_beat.PeriodicTask",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = _("schedule")
        verbose_name_plural = _("schedules")

    def is_active(self) -> bool:
        """Check if the schedule event is active."""
        return self.limit is None or self.counter < self.limit

    def periodic_task_name(self) -> str:
        """Unique task name, using to create it in celery."""
        return f"snitch-scheduled-event-task-{self.pk}"

    def creates_periodic_task_extra_kwarg(self) -> dict:
        """Creates the extra arguments for the periodic task."""
        kwargs = {"one_off": self.limit == 1, "start_time": self.start_time}
        if self.every is not None and self.period is not None:
            kwargs["interval"] = IntervalSchedule.objects.create(
                every=self.every, period=self.period
            )
        else:
            kwargs["crontab"] = CrontabSchedule.objects.create(
                minute=self.minute,
                hour=self.hour,
                day_of_week=self.day_of_week,
                day_of_month=self.day_of_month,
                month_of_year=self.month_of_year,
            )
        return kwargs

    def get_or_creates_periodic_task(self) -> PeriodicTask:
        """Gets or creates the Celery periodic task."""
        name = self.periodic_task_name()
        if not PeriodicTask.objects.filter(name=name).exists():
            task = PeriodicTask.objects.create(
                name=name,
                task="snitch.schedules.tasks.execute_schedule_task",
                **self.creates_periodic_task_extra_kwarg(),
            )
        else:
            task = PeriodicTask.objects.filter(name=name).first()
        return task

    def run(self) -> None:
        """Executes the schedule, dispatching the event."""
        # Dispatch the event using explicit dispatch
        if not self.actor:
            warnings.warn(f"The schedule {self.pk} has been executed without actor.")
        if self.is_active():
            snitch.dispatch(
                verb=self.verb,
                config={
                    "kwargs": {
                        "actor": "actor",
                        "trigger": "trigger",
                        "target": "target",
                    }
                },
            )(lambda *args, **kwargs: None)(
                actor=self.actor, trigger=self.trigger, target=self.target
            )
            # Updates the counter
            Schedule.objects.filter(pk=self.pk).update(counter=F("counter") + 1)

    def update_task(self) -> None:
        """Syncs the periodic tasks from Celery with the schedule data."""
        # Gets or create task
        if self.task:
            # Updates task fields
            self.task.one_of = self.limit == 1
            self.task.start_time = self.start_time
            # Updates interval values
            interval_fields = ["every", "period"]
            if self.task.interval:
                for interval_field in interval_fields:
                    setattr(
                        self.task.interval,
                        interval_field,
                        getattr(self, interval_field),
                    )
                self.task.interval.save()
            # Updates cron values
            cron_fields: list = [
                "minute",
                "hour",
                "day_of_week",
                "day_of_month",
                "month_of_year",
            ]
            if self.task.crontab:
                for cron_field in cron_fields:
                    setattr(
                        self.task.crontab, cron_field, getattr(self, cron_field) or "*"
                    )
                self.task.crontab.save()
            # Updates kwargs
            self.task.kwargs = f'{{"schedule_id": "{self.pk}"}}'
            # Update enabled
            self.task.enabled = self.is_active()
            # Save task
            self.task.save()

    def delete(self, **kwargs):
        # Delete the task on delete
        self.task.delete()
        return super().delete(**kwargs)

    def save(self, **kwargs) -> None:
        self.clean()
        super().save(**kwargs)
        # Creation/update of the task after the save of the model, to ensure
        # we have an ID.
        if not self.task:
            self.task = self.get_or_creates_periodic_task()
            self.update_task()
            self.save()
        else:
            self.update_task()
