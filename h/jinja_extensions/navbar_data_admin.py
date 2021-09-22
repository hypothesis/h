from copy import deepcopy

from h.security import Permission
from h.traversal import Root


def navbar_data_admin(request):
    """
    Get the navigation bar displayed at the top of the admin page.

    This is used in `templates/layouts/admin.html.jinja2`
    """

    # The ACL based system only has the admin page ACLs attached to various
    # contexts. On some of the admin pages we will have a GroupContext instead.
    # We could fix that but it won't matter soon, so we'll create a context
    # with the right ACL for now to determine which pages the user can see.
    context = Root(request)

    for tab in deepcopy(_ADMIN_MENU):
        if not request.has_permission(tab.pop("permission"), context=context):
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
        "permission": Permission.AdminPage.INDEX,
        "title": "Home",
        "route": "admin.index",
    },
    {
        "id": "admins",
        "permission": Permission.AdminPage.ADMINS,
        "title": "Administrators",
        "route": "admin.admins",
    },
    {
        "id": "badge",
        "permission": Permission.AdminPage.BADGE,
        "title": "Badge",
        "route": "admin.badge",
    },
    {
        "id": "features",
        "permission": Permission.AdminPage.FEATURES,
        "title": "Feature flags",
        "children": [
            {"route": "admin.features", "title": "Manage feature flags"},
            {"route": "admin.cohorts", "title": "Manage feature cohorts"},
        ],
    },
    {
        "id": "groups",
        "permission": Permission.AdminPage.GROUPS,
        "title": "Groups",
        "children": [
            {"route": "admin.groups", "title": "List Groups"},
            {"route": "admin.groups_create", "title": "Create a Group"},
        ],
    },
    {
        "id": "mailer",
        "permission": Permission.AdminPage.MAILER,
        "title": "Mailer",
        "route": "admin.mailer",
    },
    {
        "id": "nipsa",
        "permission": Permission.AdminPage.NIPSA,
        "title": "NIPSA",
        "route": "admin.nipsa",
    },
    {
        "id": "oauth",
        "permission": Permission.AdminPage.OAUTH_CLIENTS,
        "title": "OAuth clients",
        "route": "admin.oauthclients",
    },
    {
        "id": "organizations",
        "permission": Permission.AdminPage.ORGANIZATIONS,
        "title": "Organizations",
        "children": [
            {"route": "admin.organizations", "title": "List organizations"},
            {"route": "admin.organizations_create", "title": "Create an organization"},
        ],
    },
    {
        "id": "staff",
        "permission": Permission.AdminPage.STAFF,
        "title": "Staff",
        "route": "admin.staff",
    },
    {
        "id": "users",
        "permission": Permission.AdminPage.USERS,
        "title": "Users",
        "route": "admin.users",
    },
    {
        "id": "search",
        "permission": Permission.AdminPage.SEARCH,
        "title": "Search",
        "route": "admin.search",
    },
]
