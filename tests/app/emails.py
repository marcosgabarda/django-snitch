from django.utils.translation import gettext_lazy as _
from snitch.emails import TemplateEmailMessage


class WelcomeEmail(TemplateEmailMessage):
    """Email notification when when an user is register, to welcome."""

    default_template_name = "email.html"
    default_subject = _("Welcome!")
    use_i18n = True
