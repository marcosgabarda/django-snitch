from django.contrib import admin

from snitch.schedules.models import Schedule


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    search_fields = [
        "task__name",
        "actor_content_type",
        "trigger_content_type",
        "target_content_type",
    ]
    list_display = [
        "id",
        "actor",
        "verb",
        "trigger",
        "target",
        "counter",
        "limit",
        "created",
    ]
    list_filter = ["verb"]
    autocomplete_fields = ["task"]
