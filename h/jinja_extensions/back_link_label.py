"""A context-aware link to the previous page."""

from urllib.parse import urlparse

from h.i18n import TranslationString as _


def back_link_label(request):
    """
    Get a link which takes the user back to the previous page on the site.

    This is used in `templates/includes/back_link.html.jinja2`
    """

    referrer_path = urlparse(request.referrer or "").path
    current_username = request.user.username

    if referrer_path == request.route_path(
        "activity.user_search", username=current_username
    ):
        return _("Back to your profile page")

    if _matches_route(referrer_path, request, route_name="group_read"):
        return _("Back to group overview page")

    return None


def _matches_route(path, request, route_name):
    """Get if `path` matches the URL pattern for a given route."""

    # `route` is a pyramid.interfaces.IRoute
    route = request.registry.introspector.get("routes", route_name)["object"]
    return route.match(path) is not None
