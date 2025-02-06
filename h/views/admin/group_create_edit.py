from pyramid.view import view_config, view_defaults

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

    @view_config(request_method="GET")
    def get(self):
        return {}


@view_defaults(route_name="admin.groups_edit", **VIEW_DEFAULTS)
class AdminGroupEditViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        return {}
