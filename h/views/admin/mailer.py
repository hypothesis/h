from datetime import datetime

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from h.emails import test
from h.security import Permission
from h.tasks import mailer


@view_config(
    route_name="admin.mailer",
    request_method="GET",
    renderer="h:templates/admin/mailer.html.jinja2",
    permission=Permission.AdminPage.LOW_RISK,
)
def mailer_index(request):
    """Show the mailer test tools."""
    return {"taskid": request.params.get("taskid")}


@view_config(
    route_name="admin.mailer_test",
    request_method="POST",
    permission=Permission.AdminPage.LOW_RISK,
    require_csrf=True,
)
def mailer_test(request):
    """Send a test email."""
    if "recipient" not in request.params:
        index = request.route_path("admin.mailer")
        return HTTPSeeOther(location=index)

    mail = test.generate(request, request.params["recipient"])
    result = mailer.send.delay(*mail)
    index = request.route_path("admin.mailer", _query={"taskid": result.task_id})
    return HTTPSeeOther(location=index)


@view_config(
    route_name="admin.mailer.preview.mention_notification",
    request_method="GET",
    permission=Permission.AdminPage.LOW_RISK,
    renderer="h:templates/emails/mention_notification.html.jinja2",
)
def preview_mention_notification(_request):
    return {
        "user_url": "https://example.com/user",
        "user_display_name": "Jane Doe",
        "annotation_url": "https://example.com/bouncer",  # Bouncer link (AKA: annotation deeplink)
        "document_title": "The title",
        "document_url": "https://example.com/document",  # Document public URL
        "annotation": {
            "updated": datetime(year=2025, month=1, day=11, hour=18, minute=36),  # noqa: DTZ001
            "text": 'Hello <a data-hyp-mention data-userid="acct:user@example.com">@user</a>, how are you?',
            "text_rendered": 'Hello <a data-hyp-mention data-userid="acct:user@example.com">@user</a>, how are you?',
        },
    }
