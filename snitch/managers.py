from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.contenttypes.models import ContentType
from django.db import models

User = get_user_model()


class NotificationQuerySet(models.QuerySet):
    def accessible(self, user: AbstractBaseUser) -> "NotificationQuerySet":
        """Gets the notifications accessible by the given user."""
        if not user.is_authenticated:
            return self.none()
        return self.filter(
            receiver_id=user.pk,
            receiver_content_type=ContentType.objects.get_for_model(User),
        )

    def unread(self) -> "NotificationQuerySet":
        """Gets the unread notifications."""
        return self.filter(read=False)
