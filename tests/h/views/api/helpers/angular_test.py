# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from h.views.api.helpers.angular import AngularRouteTemplater


class TestAngularRouteTemplater(object):
    def test_static_route(self):
        def route_url(route_name, **kwargs):
            return "/" + route_name

        templater = AngularRouteTemplater(route_url, params=[])

        assert templater.route_template("foo") == "/foo"

    def test_route_with_id_placeholder(self):
        def route_url(route_name, **kwargs):
            return "/{}/{}".format(route_name, kwargs["id"])

        templater = AngularRouteTemplater(route_url, params=["id"])

        assert templater.route_template("foo") == "/foo/:id"

    def test_custom_parameter(self):
        def route_url(_, **kwargs):
            return "/things/{}".format(kwargs["thing_id"])

        templater = AngularRouteTemplater(route_url, params=["thing_id"])

        assert templater.route_template("foo") == "/things/:thing_id"

    def test_multiple_parameters(self):
        def route_url(_, **kwargs):
            return "/{}/{}".format(kwargs["foo"], kwargs["bar"])

        templater = AngularRouteTemplater(route_url, params=["foo", "bar"])

        assert templater.route_template("foo") == "/:foo/:bar"

    def test_parameter_substrings(self):
        def route_url(_, **kwargs):
            return "/api/{}/things/{}".format(kwargs["id"], kwargs["thing_id"])

        templater = AngularRouteTemplater(route_url, params=["id", "thing_id"])

        assert templater.route_template("foo") == "/api/:id/things/:thing_id"
