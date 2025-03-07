import datetime
import platform

from pyramid.renderers import render
from pyramid.request import Request

from h import __version__
from h.services.email import EmailData, EmailTag


def generate(request: Request, recipient: str) -> EmailData:
    """Generate a test email.

    :param request: the current request
    :param recipient: the recipient of the test email
    """

    context = {
        "time": datetime.datetime.utcnow().isoformat(),  # noqa: DTZ003
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "version": __version__,
    }

    text = render("h:templates/emails/test.txt.jinja2", context, request=request)
    html = render("h:templates/emails/test.html.jinja2", context, request=request)

    return EmailData(
        recipients=[recipient],
        subject="Test mail",
        body=text,
        tag=EmailTag.TEST,
        html=html,
    )
