from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from snitch.models import EventType, Event, Notification


def notify_action(modeladmin, request, queryset):
    """Explicit creates notifications for events."""
    for event in queryset:
        event.notify()
    modeladmin.message_user(request, _("Events notified!"))


notify_action.short_description = _("Notify events")


def send_action(modeladmin, request, queryset):
    """Explicit sends the notifications using the backend."""
    for notification in queryset:
        notification.send(send_async=True)
    modeladmin.message_user(request, _("Notifications sent!"))


send_action.short_description = _("Send notifications")


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "verb", "enabled"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["id", "actor", "verb", "trigger", "target", "notified", "created"]
    list_filter = ["verb", "notified"]
    actions = [notify_action]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["id", "event", "user", "read", "received", "created"]
    list_filter = ["event__verb", "read", "sent"]
    search_fields = ["user__email"]
    actions = [send_action]
    autocomplete_fields = ["user"]
