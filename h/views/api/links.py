# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.views.api.config import api_config
from h.views.api.helpers.angular import AngularRouteTemplater


@api_config(
    versions=["v1", "v2"],
    route_name="api.links",
    link_name="links",
    renderer="json_sorted",
    description="URL templates for generating URLs for HTML pages",
)
def links(context, request):
    templater = AngularRouteTemplater(request.route_url, params=["user"])

    tag_search_url = request.route_url("activity.search", _query={"q": "_query_"})
    tag_search_url = tag_search_url.replace("_query_", 'tag:":tag"')

    oauth_authorize_url = request.route_url("oauth_authorize")
    oauth_revoke_url = request.route_url("oauth_revoke")

    return {
        "account.settings": request.route_url("account"),
        "forgot-password": request.route_url("forgot_password"),
        "groups.new": request.route_url("group_create"),
        "help": request.route_url("help"),
        "oauth.authorize": oauth_authorize_url,
        "oauth.revoke": oauth_revoke_url,
        "search.tag": tag_search_url,
        "signup": request.route_url("signup"),
        "user": templater.route_template("stream.user_query"),
    }
