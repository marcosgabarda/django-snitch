import warnings
from typing import Dict, List, Optional, Union

import bleach
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import translation

from snitch.settings import ENABLED_SEND_NOTIFICATIONS
from snitch.tasks import send_email_asynchronously


class TemplateEmailMessage:
    """An object to handle emails based on templates, with automatic plain
    alternatives.
    """

    default_template_name: str = ""
    default_subject: str = ""
    default_from_email: str = ""
    fake: bool = False
    use_i18n: bool = False

    def __init__(
        self,
        to: Union[str, List],
        subject: Optional[str] = None,
        context: Optional[Dict] = None,
        from_email: Optional[str] = None,
        attaches: Optional[List] = None,
        template_name: Optional[str] = None,
        reply_to: Optional[Union[str, List]] = None,
        bcc: Optional[Union[str, List]] = None,
        cc: Optional[Union[str, List]] = None,
    ):
        self.template_name = (
            self.default_template_name if template_name is None else template_name
        )
        if not self.template_name:
            warnings.warn("You have to specify the template name")
        # Ensure these attributes are lists or tuples
        for attr_name in ["to", "reply_to", "cc", "bcc"]:
            attr = eval(attr_name)
            if (
                attr is not None
                and not isinstance(attr, list)
                and not isinstance(attr, tuple)
            ):
                setattr(self, attr_name, [attr])
            else:
                setattr(self, attr_name, attr)
        self.subject = self.default_subject if subject is None else subject
        self.from_email = self.default_from_email if from_email is None else from_email
        self.attaches = [] if attaches is None else attaches
        self.default_context = {} if context is None else context

    def get_language(self) -> str:
        """Gets the language for the email."""
        return settings.LANGUAGE_CODE

    def get_context(self) -> Dict:
        """Hook to customize context."""
        # Add default context
        current_site = Site.objects.get_current()
        self.default_context.update({"site": current_site})
        return self.default_context

    def preview(self) -> str:
        """Renders the message for a preview."""
        context = self.get_context()
        message = render_to_string(self.template_name, context, using="django")
        return message

    def async_send(self, message, message_txt):
        if not self.fake:
            send_email_asynchronously.delay(
                self.subject,
                message_txt,
                message,
                self.from_email,
                self.to,
                self.cc,
                self.bcc,
                self.reply_to,
            )
            if self.attaches:
                warnings.warn(
                    "Attaches will not added to the email, use async=False to send "
                    "attaches."
                )

    def sync_send(self, message, message_txt):
        if not self.fake:
            email = EmailMultiAlternatives(
                subject=self.subject,
                body=message_txt,
                bcc=self.bcc,
                cc=self.cc,
                from_email=self.from_email,
                to=self.to,
                reply_to=self.reply_to,
            )
            email.attach_alternative(message, "text/html")
            for attach in self.attaches:
                attach_file_name, attach_content, attach_content_type = attach
                email.attach(attach_file_name, attach_content, attach_content_type)
            email.send()

    def send(self, use_async: bool = True, language: Optional[str] = None):
        """Sends the email at the moment or using a Celery task."""
        if not ENABLED_SEND_NOTIFICATIONS:
            return

        use_async = not self.attaches and use_async
        if self.use_i18n and settings.USE_I18N:
            language = self.get_language()
            translation.activate(language)
        self.subject = "%s" % self.subject
        context = self.get_context()
        message = render_to_string(self.template_name, context, using="django")
        message_txt = message.replace("\n", "")
        message_txt = message_txt.replace("</p>", "\n")
        message_txt = message_txt.replace("</h1>", "\n\n")
        message_txt = bleach.clean(message_txt, strip=True)
        if use_async:
            self.async_send(message, message_txt)
        else:
            self.sync_send(message, message_txt)


class AdminsTemplateEmailMessage(TemplateEmailMessage):
    """Emails only for admins."""

    def __init__(
        self,
        subject: Optional[str] = None,
        context: Optional[Dict] = None,
        from_email: Optional[str] = None,
    ):
        to: Union[str, List] = [a[1] for a in settings.ADMINS]
        super().__init__(to, subject=subject, context=context, from_email=from_email)


class ManagersTemplateEmailMessage(TemplateEmailMessage):
    """Emails only for mangers."""

    def __init__(
        self, subject: str = None, context: Dict = None, from_email: str = None
    ):
        to: Union[str, List] = [manager[1] for manager in settings.MANAGERS]
        super().__init__(to, subject=subject, context=context, from_email=from_email)
