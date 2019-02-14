# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def includeme(config):
    config.add_accept_view_order("application/json")
    # If request Accept header is missing or doesn't match any registered API views,
    # by default we want to use the view that is configured for "application/json".
    # This will be the current-version API view for the route.
    for version in config.registry.settings["api.versions"]:
        config.add_accept_view_order(
            "application/vnd.hypothesis." + version + "+json",
            weighs_less_than="application/json",
        )
    config.scan(__name__)
