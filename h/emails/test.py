import datetime
import platform

from pyramid.renderers import render

from h import __version__


def generate(request, recipient):
    """
    Generate a test email.

    :param request: the current request
    :type request: pyramid.request.Request
    :param recipient: the recipient of the test email
    :type recipient: str

    :returns: a 4-element tuple containing: recipients, subject, text, html
    """

    context = {
        "time": datetime.datetime.utcnow().isoformat(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "version": __version__,
    }

    text = render("h:templates/emails/test.txt.jinja2", context, request=request)
    html = render("h:templates/emails/test.html.jinja2", context, request=request)

    return [recipient], "Test mail", text, html
