from pyramid.httpexceptions import HTTPNoContent

from h import links
from h.emails import flag_notification
from h.security import Permission
from h.tasks import mailer
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

    _email_group_admin(request, context.annotation)

    return HTTPNoContent()


def _email_group_admin(request, annotation):
    incontext_link = links.incontext_link(request, annotation)
    if incontext_link is None:
        incontext_link = annotation.target_uri

    group = annotation.group
    if group.creator and group.creator.email:
        send_params = flag_notification.generate(
            request, group.creator.email, incontext_link
        )
        mailer.send.delay(*send_params)
