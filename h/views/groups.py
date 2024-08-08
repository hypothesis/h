from pyramid import httpexceptions
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

    @view_config(route_name="group_create", request_method="GET")
    def create(self):
        """Render the page for creating a new group."""
        return {
            "page_title": "Create a new private group",
            "mode": "create",
            "group": {
                "pubid": "",
                "name": "",
                "description": "",
                "link": "",
            },
        }

    @view_config(
        route_name="group_edit", request_method="GET", permission=Permission.Group.EDIT
    )
    def edit(self):
        """Render the page for editing an existing group."""
        group = self.context.group

        return {
            "page_title": "Edit group details",
            "mode": "edit",
            "group": {
                "pubid": group.pubid,
                "name": group.name,
                "description": group.description,
                "link": self.request.route_url(
                    "group_read", pubid=group.pubid, slug=group.slug
                ),
            },
        }


@view_config(route_name="group_read_noslug", request_method="GET")
def read_noslug(context, request):
    check_slug(context.group, request)


def check_slug(group, request):
    """Redirect if the request slug does not match that of the group."""
    slug = request.matchdict.get("slug")
    if slug is None or slug != group.slug:
        path = request.route_path("group_read", pubid=group.pubid, slug=group.slug)
        raise httpexceptions.HTTPMovedPermanently(path)
