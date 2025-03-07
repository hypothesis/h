from pyramid.renderers import render
from pyramid.request import Request

from h.i18n import TranslationString as _
from h.services.email import EmailData, EmailTag


def generate(
    request: Request, user_id: int, email: str, activation_code: str
) -> EmailData:
    """Generate an email for a user signup.

    :param request: the current request
    :param user_id: the new user's primary key ID
    :param email: the new user's email address
    :param activation_code: the activation code
    """
    context = {
        "activate_link": request.route_url("activate", id=user_id, code=activation_code)
    }

    subject = _("Please activate your account")

    text = render("h:templates/emails/signup.txt.jinja2", context, request=request)
    html = render("h:templates/emails/signup.html.jinja2", context, request=request)

    return EmailData(
        recipients=[email],
        subject=subject,
        body=text,
        tag=EmailTag.ACTIVATION,
        html=html,
    )
