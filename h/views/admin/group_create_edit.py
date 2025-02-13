from colander import Invalid
from pyramid.csrf import get_csrf_token
from pyramid.httpexceptions import HTTPFound
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
        self.organizations = {
            o.pubid: o
            for o in self.request.find_service(
                name="list_organizations"
            ).organizations()
        }
        self.default_organization = self.request.find_service(
            name="organization"
        ).get_default()
        self.user_svc = self.request.find_service(name="user")
        self.group_create_svc = request.find_service(name="group_create")
        self.group_members_svc = request.find_service(name="group_members")

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

        cstruct = self.request.POST.mixed()

        # cstruct["scopes"] and cstruct["members"] will either be:
        # - Missing entirely (if the user didn't submit any scopes or members)
        # - A single string (if the user submitted only a single scope or member)
        # - A list of strings (if the user submitted multiple scopes or members)
        # Replace entirely missing scopes or members with empty lists,
        # and single strings with lists of one string.
        cstruct["scopes"] = self.request.POST.getall("scopes")
        cstruct["members"] = self.request.POST.getall("members")

        try:
            appstruct = schema.deserialize(cstruct)
        except Invalid as err:
            return {
                "js_config": self.js_config(
                    group={
                        "type": cstruct.get("group_type"),
                        "name": cstruct.get("name"),
                        "organization": cstruct.get("organization"),
                        "creator": cstruct.get("creator"),
                        "description": cstruct.get("description"),
                        "enforceScope": bool(cstruct.get("enforce_scope", False) == "on"),
                        "scopes": cstruct.get("scopes"),
                        "memberships": cstruct.get("scopes"),
                    },
                    validation_error=err,
                )
            }

        organization = self.organizations.get(appstruct["organization"])

        creator = self.user_svc.fetch(
            appstruct["creator"],
            (
                organization.authority
                if organization
                else self.request.default_authority
            ),
        )

        group_type = appstruct["group_type"]

        group_create_function = {
            "open": self.group_create_svc.create_open_group,
            "restricted": self.group_create_svc.create_restricted_group,
        }[group_type]

        group = group_create_function(
            name=appstruct["name"],
            userid=creator.userid,
            scopes=appstruct["scopes"],
            description=appstruct["description"],
            organization=organization,
            enforce_scope=appstruct["enforce_scope"],
        )

        members = [
            self.user_svc.fetch(username, organization.authority)
            for username in appstruct["members"]
        ]

        self.group_members_svc.add_members(group, [member.userid for member in members])

        self.request.session.flash(f"Created new group: '{group.name}'", "success")

        return HTTPFound(location=self.request.route_url("admin.groups"))

    def js_config(self, group: dict | None = None, validation_error: Invalid = None):
        js_config = {
            "styles": self.request.registry["assets_env"].urls("admin_css"),
            "CSRFToken": get_csrf_token(self.request),
            "context": {
                "group": group or {},
                "user": {
                    "username": self.request.user.username,
                },
                "organizations": [
                    {
                        "label": f"{organization.name} ({organization.authority})",
                        "pubid": organization.pubid,
                    }
                    for organization in self.organizations.values()
                ],
                "defaultOrganization": {"pubid": self.default_organization.pubid},
            },
        }

        if validation_error:
            js_config["context"]["errors"] = validation_error.asdict()

        return js_config


@view_defaults(route_name="admin.groups_edit", **VIEW_DEFAULTS)
class AdminGroupEditViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @view_config(request_method="GET")
    def get(self):
        return {"js_config": {}}
