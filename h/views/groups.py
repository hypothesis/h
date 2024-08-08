from pyramid import httpexceptions
from pyramid.view import view_config, view_defaults

from h import form, i18n
from h.schemas.forms.group import group_schema
from h.security import Permission

_ = i18n.TranslationString


@view_defaults(
    route_name="group_create",
    renderer="h:templates/groups/create.html.jinja2",
    is_authenticated=True,
)
class GroupCreateController:
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        """Render the page for creating a new group."""
        return {}


@view_defaults(
    route_name="group_edit",
    renderer="h:templates/groups/edit.html.jinja2",
    permission=Permission.Group.EDIT,
)
class GroupEditController:
    def __init__(self, context, request):
        self.group = context.group
        self.request = request
        self.schema = group_schema().bind(request=self.request)
        self.form = request.create_form(
            self.schema, buttons=(_("Save"),), use_inline_editing=True
        )

    @view_config(request_method="GET")
    def get(self):
        self.form.set_appstruct(
            {"name": self.group.name or "", "description": self.group.description or ""}
        )

        return self._template_data()

    @view_config(request_method="POST")
    def post(self):
        return form.handle_form_submission(
            self.request,
            self.form,
            on_success=self._update_group,
            on_failure=self._template_data,
        )

    def _template_data(self):
        return {
            "form": self.form.render(),
            "group_path": self.request.route_path(
                "group_read", pubid=self.group.pubid, slug=self.group.slug
            ),
        }

    def _update_group(self, appstruct):
        self.group.name = appstruct["name"]
        self.group.description = appstruct["description"]


@view_config(route_name="group_read_noslug", request_method="GET")
def read_noslug(context, request):
    check_slug(context.group, request)


def check_slug(group, request):
    """Redirect if the request slug does not match that of the group."""
    slug = request.matchdict.get("slug")
    if slug is None or slug != group.slug:
        path = request.route_path("group_read", pubid=group.pubid, slug=group.slug)
        raise httpexceptions.HTTPMovedPermanently(path)
