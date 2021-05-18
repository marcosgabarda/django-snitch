from typing import List, Optional, Union

from celery import shared_task
from django.core.mail import EmailMultiAlternatives

from snitch.helpers import get_notification_model


@shared_task(serializer="json")
def send_notification_task(notification_pk: int) -> Optional[bool]:
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
    to: Union[List, str],
    cc: Optional[List],
    bcc: Optional[List],
    reply_to: Optional[List],
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
