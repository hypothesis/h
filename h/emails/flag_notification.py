from pyramid.renderers import render
from pyramid.request import Request

from h.i18n import TranslationString as _
from h.models import User
from h.services.email import EmailLogData, EmailTag


def generate(
    request: Request, users: list[User], incontext_link: str, annotation_id: str
):
    """
    Generate an email to notify the group admin when a group member flags an annotation.

    :param request: the current request
    :param users: the group admins
    :param incontext_link: the direct link to the flagged annotation

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """
    context = {"incontext_link": incontext_link}

    subject = _("An annotation has been flagged")

    text = render(
        "h:templates/emails/flag_notification.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/flag_notification.html.jinja2", context, request=request
    )

    log_data = EmailLogData(
        tag=EmailTag.FLAG_NOTIFICATION,
        recipient_ids=[user.id for user in users],
        annotation_id=annotation_id,
    )

    emails = [user.email for user in users]
    return emails, subject, text, EmailTag.FLAG_NOTIFICATION, html, log_data
