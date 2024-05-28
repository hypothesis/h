"""The navigation bar displayed at the top of most pages."""

from h.i18n import TranslationString as _


def navbar_data(request):
    """
    Get the navigation bar displayed at the top of the page.

    This is used in `templates/includes/navbar.html.jinja2`
    """

    user_activity_url = None
    username = None

    if request.user:
        user_activity_url = request.route_url(
            "activity.user_search", username=request.user.username
        )
        username = request.user.username

    # Make all groups associated with the user visible in the search auto complete.
    groups = request.find_service(name="group_list").associated_groups(request.user)

    return {
        "create_group_item": {
            "title": _("Create new group"),
            "link": request.route_url("group_create"),
        },
        "groups_menu_items": [
            {
                "title": group.name,
                "link": request.route_url(
                    "group_read", pubid=group.pubid, slug=group.slug
                ),
            }
            for group in groups
        ],
        "groups_suggestions": [
            {
                "name": group.name,
                "pubid": group.pubid,
                "relationship": (
                    "Creator"
                    if group.creator and group.creator.username == username
                    else None
                ),
            }
            for group in groups
        ],
        "q": request.params.get("q", ""),
        "search_url": _get_search_url(request),
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
        "username": username,
        "username_url": user_activity_url,
    }


def _get_search_url(request):
    if request.matched_route and request.matched_route.name in [
        "group_read",
        "activity.user_search",
    ]:
        return request.current_route_url()

    return request.route_url("activity.search")
