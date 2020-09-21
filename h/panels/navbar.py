"""The navigation bar displayed at the top of most pages."""

from pyramid_layout.panel import panel_config

from h.i18n import TranslationString as _  # noqa


@panel_config(name="navbar", renderer="h:templates/panels/navbar.html.jinja2")
def navbar(context, request, search=None, opts=None):
    """
    The navigation bar displayed at the top of the page.

    :param search: The current page's search state, if relevant.
    :type search: h.activity.query.ActivityResults
    """

    groups_menu_items = []
    groups_suggestions = []
    user_activity_url = None
    username = None

    if request.user:
        user_activity_url = request.route_url(
            "activity.user_search", username=request.user.username
        )
        username = request.user.username
    # Make all groups associated with the user visible in the search auto complete.
    list_group_service = request.find_service(name="group_list")
    groups = list_group_service.associated_groups(request.user)

    def _relationship(group, username):
        if group.creator == username:
            return "Creator"
        return None

    groups_menu_items = [
        {
            "title": group.name,
            "link": request.route_url("group_read", pubid=group.pubid, slug=group.slug),
        }
        for group in groups
    ]
    groups_suggestions = [
        {
            "name": group.name,
            "pubid": group.pubid,
            "relationship": _relationship(group, request.user),
        }
        for group in groups
    ]

    route = request.matched_route

    if route and route.name in ["group_read", "activity.user_search"]:
        search_url = request.current_route_url()
    else:
        search_url = request.route_url("activity.search")

    return {
        "settings_menu_items": [
            {"title": _("Account details"), "link": request.route_url("account")},
            {"title": _("Edit profile"), "link": request.route_url("account_profile")},
            {
                "title": _("Notifications"),
                "link": request.route_url("account_notifications"),
            },
            {"title": _("Developer"), "link": request.route_url("account_developer")},
        ],
        "signout_item": {"title": _("Sign out"), "link": request.route_url("logout")},
        "groups_menu_items": groups_menu_items,
        "groups_suggestions": groups_suggestions,
        "create_group_item": {
            "title": _("Create new group"),
            "link": request.route_url("group_create"),
        },
        "username": username,
        "username_url": user_activity_url,
        "search": search,
        "search_url": search_url,
        "q": request.params.get("q", ""),
        "opts": opts or {},
    }
