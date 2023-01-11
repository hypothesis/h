from copy import deepcopy

from h.security import Permission


def navbar_data_admin(request):
    """
    Get the navigation bar displayed at the top of the admin page.

    This is used in `templates/layouts/admin.html.jinja2`
    """

    for tab in deepcopy(_ADMIN_MENU):
        if not request.has_permission(tab.pop("permission")):
            continue

        if route := tab.get("route"):
            tab["url"] = request.route_url(route)

        if children := tab.get("children"):
            for child in children:
                child["url"] = request.route_url(child["route"])

        yield tab


_ADMIN_MENU = [
    {
        "id": "index",
        "permission": Permission.AdminPage.LOW_RISK,
        "title": "Home",
        "route": "admin.index",
    },
    {
        "id": "admins",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "Administrators",
        "route": "admin.admins",
    },
    {
        "id": "badge",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "Badge",
        "route": "admin.badge",
    },
    {
        "id": "documents",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "Documents",
        "route": "admin.documents",
    },
    {
        "id": "features",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "Feature flags",
        "children": [
            {"route": "admin.features", "title": "Manage feature flags"},
            {"route": "admin.cohorts", "title": "Manage feature cohorts"},
        ],
    },
    {
        "id": "groups",
        "permission": Permission.AdminPage.LOW_RISK,
        "title": "Groups",
        "children": [
            {"route": "admin.groups", "title": "List Groups"},
            {"route": "admin.groups_create", "title": "Create a Group"},
        ],
    },
    {
        "id": "mailer",
        "permission": Permission.AdminPage.LOW_RISK,
        "title": "Mailer",
        "route": "admin.mailer",
    },
    {
        "id": "nipsa",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "NIPSA",
        "route": "admin.nipsa",
    },
    {
        "id": "oauth",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "OAuth clients",
        "route": "admin.oauthclients",
    },
    {
        "id": "organizations",
        "permission": Permission.AdminPage.LOW_RISK,
        "title": "Organizations",
        "children": [
            {"route": "admin.organizations", "title": "List organizations"},
            {"route": "admin.organizations_create", "title": "Create an organization"},
        ],
    },
    {
        "id": "staff",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "Staff",
        "route": "admin.staff",
    },
    {
        "id": "users",
        "permission": Permission.AdminPage.LOW_RISK,
        "title": "Users",
        "route": "admin.users",
    },
    {
        "id": "search",
        "permission": Permission.AdminPage.HIGH_RISK,
        "title": "Search",
        "route": "admin.search",
    },
]
