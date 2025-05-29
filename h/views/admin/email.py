from dataclasses import asdict  # noqa: A005

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import view_config

from h.emails import test
from h.models.annotation import ModerationStatus
from h.security import Permission
from h.services.annotation_moderation import AnnotationModerationService
from h.services.email import TaskData
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
    task_data = TaskData(tag=email_data.tag, sender_id=request.user.id)
    result = email.send.delay(asdict(email_data), asdict(task_data))
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


@view_config(
    route_name="admin.email.preview.annotation_moderation_notification",
    request_method="GET",
    permission=Permission.AdminPage.LOW_RISK,
    renderer="h:templates/emails/annotation_moderation_notification.html.jinja2",
)
def preview_annotation_moderation_notification(_request):
    return {
        "user_display_name": "Jane Doe",
        "status_change_description": AnnotationModerationService.email_status_change_description(
            "GROUP NAME", ModerationStatus.APPROVED
        ),
        "annotation_url": "https://example.com/bouncer",  # Bouncer link (AKA: annotation deeplink)
        "annotation": {
            "text_rendered": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla tincidunt malesuada ex, id dictum risus posuere sed. Curabitur risus lectus, aliquam vel tempus ut, tempus non risus. Duis ac nibh lacinia, lacinia leo sit amet, lacinia tortor. Vestibulum dictum maximus lorem, nec lobortis augue ullamcorper nec. Ut ac viverra nisi. Nam congue neque eu mi viverra ultricies. Integer pretium odio nulla, at semper dolor tincidunt quis. Pellentesque suscipit magna nec nunc mollis, a interdum purus aliquam.",
        },
        "annotation_quote": "This is a very important text",
    }
