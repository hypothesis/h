from pyramid.renderers import render
from pyramid.request import Request

from h.i18n import TranslationString as _
from h.models import User
from h.services.email import EmailData, EmailTag


def generate(request: Request, user: User) -> EmailData:
    """Generate an email for a user password reset request.

    :param request: the current request
    :param user: the user to whom to send the reset code
    """
    serializer = request.registry.password_reset_serializer
    code = serializer.dumps(user.username)
    context = {
        "username": user.username,
        "reset_code": code,
        "reset_link": request.route_url("account_reset_with_code", code=code),
    }

    subject = _("Reset your password")

    text = render(
        "h:templates/emails/reset_password.txt.jinja2", context, request=request
    )
    html = render(
        "h:templates/emails/reset_password.html.jinja2", context, request=request
    )

    return EmailData(
        recipients=[user.email],  # type: ignore[list-item]
        subject=subject,
        body=text,
        tag=EmailTag.RESET_PASSWORD,
        html=html,
    )
