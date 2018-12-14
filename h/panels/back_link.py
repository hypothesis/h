# -*- coding: utf-8 -*-

"""A context-aware link to the previous page."""

from __future__ import unicode_literals

from pyramid_layout.panel import panel_config

from h._compat import urlparse
from h.i18n import TranslationString as _  # noqa


@panel_config(name="back_link", renderer="h:templates/panels/back_link.html.jinja2")
def back_link(context, request):
    """
    A link which takes the user back to the previous page on the site.
    """

    referrer_path = urlparse.urlparse(request.referrer or "").path
    current_username = request.user.username

    if referrer_path == request.route_path(
        "activity.user_search", username=current_username
    ):
        back_label = _("Back to your profile page")
    elif _matches_route(referrer_path, request, "group_read"):
        back_label = _("Back to group overview page")
    else:
        back_label = None

    return {"back_label": back_label, "back_location": request.referrer}


def _matches_route(path, request, route_name):
    """
    Return ``True`` if ``path`` matches the URL pattern for a given route.
    """

    introspector = request.registry.introspector

    # `route` is a pyramid.interfaces.IRoute
    route = introspector.get("routes", route_name)["object"]
    return route.match(path) is not None
