# -*- coding: utf-8 -*-
"""
Support for providing Angular-compatible routes for the client.
"""

from __future__ import unicode_literals


class AngularRouteTemplater(object):
    """
    Create Angular-compatible templates for named routes.

    The template format here is designed to be compatible with ``ngResource``.
    These templates are of the form:

        /api/thing/:id

    where `:id` is a placeholder for an ID parameter.

    See: https://docs.angularjs.org/api/ngResource/service/$resource

    """

    class URLParameter(object):
        def __init__(self, name):
            self.name = name

        @property
        def url_safe(self):
            return "__{}__".format(self.name)

        @property
        def placeholder(self):
            return ":{}".format(self.name)

    def __init__(self, route_url, params):
        """Instantiate the templater with a route-generating function.

        Typically, the route-generating function will be ``request.route_url``,
        but can be any function that takes a route name and keyword arguments
        and returns a URL.

        A list of known parameter names must also be provided, so that the
        templater can pass the appropriate keyword arguments into the route
        generator.
        """
        self._route_url = route_url

        self._params = [self.URLParameter(p) for p in params]

    def route_template(self, route_name):
        """Generate a templated version of a named route."""

        route_kwargs = {p.name: p.url_safe for p in self._params}

        # We can't just use the colon-delimited placeholder (e.g. `:id`),
        # because the colon will be URL-encoded. Therefore, we use a URL-safe
        # placeholder and substitute back the value we want later.
        url_safe_template = self._route_url(route_name, **route_kwargs)

        template = url_safe_template

        for param in self._params:
            template = template.replace(param.url_safe, param.placeholder)

        return template
