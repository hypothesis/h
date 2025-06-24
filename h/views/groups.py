from pyramid import httpexceptions
from pyramid.csrf import get_csrf_token
from pyramid.view import view_config, view_defaults

from h import i18n
from h.security import Permission

_ = i18n.TranslationString


@view_defaults(
    renderer="h:templates/groups/create_edit.html.jinja2", is_authenticated=True
)
class GroupCreateEditController:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.annotation_stats_service = request.find_service(name="annotation_stats")

    @view_config(route_name="group_create", request_method="GET")
    def create(self):
        """Render the page for creating a new group."""

        if self.request.feature("group_type"):
            page_title = "Create a new group"
        else:
            page_title = "Create a new private group"

        return {
            "page_title": page_title,
            "js_config": self._js_config(),
        }

    @view_config(
        route_name="group_edit", request_method="GET", permission=Permission.Group.EDIT
    )
    @view_config(
        route_name="group_edit_members",
        request_method="GET",
        permission=Permission.Group.EDIT,
    )
    @view_config(
        route_name="group_moderation",
        request_method="GET",
        permission=Permission.Group.EDIT,
    )
    def edit(self):
        """Render the page for editing an existing group."""
        return {
            "page_title": "Edit group",
            "js_config": self._js_config(),
        }

    def _js_config(self):
        csrf_token = get_csrf_token(self.request)

        def api_config(route_name: str, method: str, **kw):
            return {
                "method": method,
                "url": self.request.route_url(route_name, **kw),
                "headers": {"X-CSRF-Token": csrf_token},
            }

        js_config = {
            "styles": self.request.registry["assets_env"].urls("forms_css"),
            "api": {
                "createGroup": api_config("api.groups", "POST"),
            },
            "context": {
                "group": None,
                "user": {
                    "userid": self.request.authenticated_userid,
                },
            },
            "features": {
                "group_members": self.request.feature("group_members"),
                "group_type": self.request.feature("group_type"),
                "group_moderation": self.request.feature("group_moderation"),
                "pre_moderation": self.request.feature("pre_moderation"),
            },
        }

        if group := getattr(self.context, "group", None):
            js_config["context"]["group"] = {
                "pubid": group.pubid,
                "name": group.name,
                "description": group.description,
                "type": group.type,
                "link": self.request.route_url(
                    "group_read", pubid=group.pubid, slug=group.slug
                ),
                "num_annotations": self.annotation_stats_service.total_group_annotation_count(
                    group.pubid, unshared=False
                ),
                "pre_moderated": group.pre_moderated,
            }
            js_config["api"].update(
                {
                    "updateGroup": api_config("api.group", "PATCH", id=group.pubid),
                    "readGroupMembers": api_config(
                        "api.group_members", "GET", pubid=group.pubid
                    ),
                    "editGroupMember": api_config(
                        "api.group_member", "PATCH", pubid=group.pubid, userid=":userid"
                    ),
                    "removeGroupMember": api_config(
                        "api.group_member",
                        "DELETE",
                        pubid=group.pubid,
                        userid=":userid",
                    ),
                    "groupAnnotations": api_config(
                        "api.group_annotations", "GET", pubid=group.pubid
                    ),
                    "annotationModeration": api_config(
                        "api.annotation_moderation", "PATCH", id=":annotationId"
                    ),
                }
            )

        return js_config


@view_config(route_name="group_read_noslug", request_method="GET")
def read_noslug(context, request):
    check_slug(context.group, request)


def check_slug(group, request):
    """Redirect if the request slug does not match that of the group."""
    slug = request.matchdict.get("slug")
    if slug is None or slug != group.slug:
        path = request.route_path("group_read", pubid=group.pubid, slug=group.slug)
        raise httpexceptions.HTTPMovedPermanently(path)
