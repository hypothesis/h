from pyramid.csrf import get_csrf_token
from pyramid.view import view_config, view_defaults

from h.schemas.forms.admin.group import AdminGroupSchema
from h.security import Permission

VIEW_DEFAULTS = {
    "renderer": "h:templates/admin/group_create_edit.html.jinja2",
    "permission": Permission.AdminPage.LOW_RISK,
}


@view_defaults(route_name="admin.groups_create", **VIEW_DEFAULTS)
class AdminGroupCreateViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

        list_organizations_svc = self.request.find_service(name="list_organizations")
        self.organizations = {
            o.pubid: o for o in list_organizations_svc.organizations()
        }

        self.user_svc = self.request.find_service(name="user")

    @view_config(request_method="GET")
    def get(self):
        return {"js_config": self.js_config()}

    @view_config(request_method="POST")
    def post(self):
        schema = AdminGroupSchema().bind(
            request=self.request,
            organizations=self.organizations,
            user_svc=self.user_svc,
        )

        schema.deserialize(self.request.POST)

        return {"js_config": {}}

    def js_config(self):
        return {
            "styles": self.request.registry["assets_env"].urls("admin_css"),
            "CSRFToken": get_csrf_token(self.request),
        }


@view_defaults(route_name="admin.groups_edit", **VIEW_DEFAULTS)
class AdminGroupEditViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        return {"js_config": {}}
