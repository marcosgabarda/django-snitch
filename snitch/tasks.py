from celery import shared_task
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives

from snitch.helpers import get_notification_model


@shared_task(serializer="json")
def create_notification_task(
    event_pk: int, receiver_id: int, receiver_content_type_id: int
) -> int | None:
    ContentType = apps.get_model("contenttypes.ContentType")
    Event = apps.get_model("snitch.Event")
    Notification = get_notification_model()
    try:
        event = Event.objects.get(pk=event_pk)
        receiver_content_type = ContentType.objects.get(pk=receiver_content_type_id)
        receiver = receiver_content_type.get_object_for_this_type(pk=receiver_id)
    except ObjectDoesNotExist:
        return None
    notification = Notification(event=event, receiver=receiver)
    notification.save()
    return notification.pk


@shared_task(serializer="json")
def send_notification_task(notification_pk: int) -> bool | None:
    """A Celery task to send push notifications related with a given Notification
    model."""

    Notification = get_notification_model()

    try:
        notification = Notification.objects.get(pk=notification_pk)
    except Notification.DoesNotExist:
        return False
    notification.send(send_async=False)
    return None


@shared_task(serializer="json")
def send_email_asynchronously(
    subject: str,
    message_txt: str,
    message: str,
    from_email: str,
    to: list | str,
    cc: list | None,
    bcc: list | None,
    reply_to: list | None,
):
    """Sends an email as a asynchronous task."""
    email = EmailMultiAlternatives(
        subject=subject,
        body=message_txt,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
    )
    email.attach_alternative(message, "text/html")
    email.send()
    return True
