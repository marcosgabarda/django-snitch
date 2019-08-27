from celery.task import task
from django.core.mail import EmailMultiAlternatives


@task(serializer="json")
def push_task(notification_pk):
    """A Celery task to send push notifications related with a given Notification
    model."""
    from snitch.helpers import get_notification_model

    Notification = get_notification_model()

    try:
        notification = Notification.objects.get(pk=notification_pk)
    except Notification.DoesNotExist:
        return False
    notification.push(send_async=False)


@task(serializer="json")
def send_email_asynchronously(subject, message_txt, message, from_email, to):
    """Sends an email as a asynchronous task."""
    email = EmailMultiAlternatives(
        subject=subject, body=message_txt, from_email=from_email, to=to
    )
    email.attach_alternative(message, "text/html")
    email.send()
