# -*- coding: utf-8 -*-

from pyramid.view import view_config


@view_config(
    route_name="organization_logo", request_method="GET", renderer="svg", http_cache=600
)
def organization_logo(logo, request):
    return logo
