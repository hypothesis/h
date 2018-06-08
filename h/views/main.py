# -*- coding: utf-8 -*-

"""
Core application views.

Important views which don't form part of any other major feature package.
"""

from __future__ import unicode_literals

import logging

from pyramid import httpexceptions
from pyramid import response
from pyramid.view import view_config

from h.views.client import sidebar_app
from h.util.user import split_user

log = logging.getLogger(__name__)


@view_config(
    route_name="annotation",
    permission="read",
    renderer="h:templates/app.html.jinja2",
    csp_insecure_optout=True,
)
def annotation_page(context, request):
    annotation = context.annotation
    document = annotation.document
    if document and document.title:
        title = "Annotation by {user} on {title}".format(
            user=annotation.userid.replace("acct:", ""), title=document.title
        )
    else:
        title = "Annotation by {user}".format(
            user=annotation.userid.replace("acct:", "")
        )

    alternate = request.route_url("api.annotation", id=annotation.id)

    return sidebar_app(
        request,
        {
            "meta_attrs": (
                {"property": "og:title", "content": title},
                {"property": "og:description", "content": ""},
                {"property": "og:image", "content": "/assets/images/logo.png"},
                {"property": "og:site_name", "content": "Hypothes.is"},
                {"property": "og:url", "content": request.url},
            ),
            "link_attrs": (
                {"rel": "alternate", "href": alternate, "type": "application/json"},
            ),
        },
    )


@view_config(route_name="robots", http_cache=(86400, {"public": True}))
def robots(context, request):
    return response.FileResponse(
        "h/static/robots.txt", request=request, content_type=b"text/plain"
    )


@view_config(
    route_name="stream",
    renderer="h:templates/app.html.jinja2",
    csp_insecure_optout=True,
)
def stream(context, request):
    q = request.params.get("q", "").split(":", 1)
    if len(q) >= 2 and q[0] == "tag":
        tag = q[1]
        if " " in tag:
            tag = '"' + tag + '"'
        query = {"q": "tag:{}".format(tag)}
        location = request.route_url("activity.search", _query=query)
        raise httpexceptions.HTTPFound(location=location)
    atom = request.route_url("stream_atom")
    rss = request.route_url("stream_rss")
    return sidebar_app(
        request,
        {
            "link_tags": [
                {"rel": "alternate", "href": atom, "type": "application/atom+xml"},
                {"rel": "alternate", "href": rss, "type": "application/rss+xml"},
            ]
        },
    )


@view_config(route_name="stream.tag_query")
def stream_tag_redirect(request):
    query = {"q": "tag:{}".format(request.matchdict["tag"])}
    location = request.route_url("stream", _query=query)
    raise httpexceptions.HTTPFound(location=location)


@view_config(route_name="stream.user_query")
def stream_user_redirect(request):
    """
    Redirect to a user's activity page.
    """

    user = request.matchdict["user"]

    # The client generates /u/ links which include the full account ID
    if user.startswith("acct:"):
        try:
            user = split_user(user)["username"]
        except ValueError:
            # If it's not a valid userid, catch the exception and just treat
            # the parameter as a literal username.
            pass

    location = request.route_url("activity.user_search", username=user)

    raise httpexceptions.HTTPFound(location=location)
