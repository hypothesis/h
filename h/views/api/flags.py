from dataclasses import asdict

from pyramid.httpexceptions import HTTPNoContent

from h import links
from h.emails import flag_notification
from h.security import Permission
from h.security.permission_map import GROUP_MODERATE_PREDICATES
from h.services.email import TaskData
from h.tasks import email
from h.views.api.config import api_config


@api_config(
    versions=["v1", "v2"],
    route_name="api.annotation_flag",
    request_method="PUT",
    link_name="annotation.flag",
    description="Flag an annotation for review",
    permission=Permission.Annotation.FLAG,
)
def create(context, request):
    request.find_service(name="flag").create(request.user, context.annotation)

    _email_group_moderators(request, context.annotation)

    return HTTPNoContent()


def _email_group_moderators(request, annotation):
    incontext_link = links.incontext_link(request, annotation)
    if incontext_link is None:
        incontext_link = annotation.target_uri

    group_members_service = request.find_service(name="group_members")

    memberships = group_members_service.get_memberships(
        annotation.group, roles=list(GROUP_MODERATE_PREDICATES.keys())
    )

    for membership in memberships:
        if user_email := membership.user.email:
            email_data = flag_notification.generate(request, user_email, incontext_link)
            task_data = TaskData(
                tag=email_data.tag,
                sender_id=request.user.id,
                recipient_ids=[membership.user.id],
                extra={"annotation_id": annotation.id},
            )
            email.send.delay(asdict(email_data), asdict(task_data))
