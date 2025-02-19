from pyramid.renderers import render
from pyramid.request import Request

from h.i18n import TranslationString as _
from h.services.email import EmailData, EmailTag


def generate(request: Request, email: str, incontext_link: str) -> EmailData:
    """Generate an email to notify the group admin when a group member flags an annotation.

    :param request: the current request
    :param email: the group admin's email address
    :param incontext_link: the direct link to the flagged annotation
    """
    context = {"incontext_link": incontext_link}

    subject = _("An annotation has been flagged")

    text = render(
        "h:templates/emails/flag_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/flag_notification.html.jinja2", context, request=request
    )

    return EmailData(
        recipients=[email],
        subject=subject,
        body=text,
        tag=EmailTag.FLAG_NOTIFICATION,
        html=html,
    )
