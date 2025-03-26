from dataclasses import asdict  # noqa: A005

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from h.emails import test
from h.security import Permission
from h.services.email import LogData
from h.tasks import email


@view_config(
    route_name="admin.email",
    request_method="GET",
    renderer="h:templates/admin/email.html.jinja2",
    permission=Permission.AdminPage.LOW_RISK,
)
def email_index(request):
    """Show the email test tools."""
    return {"taskid": request.params.get("taskid")}


@view_config(
    route_name="admin.email_test",
    request_method="POST",
    permission=Permission.AdminPage.LOW_RISK,
    require_csrf=True,
)
def email_test(request):
    """Send a test email."""
    if "recipient" not in request.params:
        index = request.route_path("admin.email")
        return HTTPSeeOther(location=index)

    email_data = test.generate(request, request.params["recipient"])
    log_data = LogData(
        tag=email_data.tag,
        sender_id=request.user.id,
    )
    result = email.send.delay(asdict(email_data), asdict(log_data))
    index = request.route_path("admin.email", _query={"taskid": result.task_id})
    return HTTPSeeOther(location=index)


@view_config(
    route_name="admin.email.preview.mention_notification",
    request_method="GET",
    permission=Permission.AdminPage.LOW_RISK,
    renderer="h:templates/emails/mention_notification.html.jinja2",
)
def preview_mention_notification(_request):
    return {
        "username": "janedoe",
        "user_display_name": "Jane Doe",
        "annotation_url": "https://example.com/bouncer",  # Bouncer link (AKA: annotation deeplink)
        "document_title": "The document",
        "document_url": "https://example.com/document",  # Document public URL
        "annotation": {
            "text_rendered": 'Hello <a data-hyp-mention data-userid="acct:user@example.com">@user</a>, how are you?',
        },
        "annotation_quote": "This is a very important text",
    }
