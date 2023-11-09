from h.views.api.helpers.angular import AngularRouteTemplater


class TestAngularRouteTemplater:
    def test_static_route(self):
        def route_url(route_name, **kwargs):  # pylint:disable=unused-argument
            return "/" + route_name

        templater = AngularRouteTemplater(route_url, params=[])

        assert templater.route_template("foo") == "/foo"

    def test_route_with_id_placeholder(self):
        def route_url(route_name, **kwargs):
            return f"/{route_name}/{kwargs['id']}"

        templater = AngularRouteTemplater(route_url, params=["id"])

        assert templater.route_template("foo") == "/foo/:id"

    def test_custom_parameter(self):
        def route_url(_, **kwargs):
            return f"/things/{kwargs['thing_id']}"

        templater = AngularRouteTemplater(route_url, params=["thing_id"])

        assert templater.route_template("foo") == "/things/:thing_id"

    def test_multiple_parameters(self):
        def route_url(_, **kwargs):
            return f"/{kwargs['foo']}/{kwargs['bar']}"

        templater = AngularRouteTemplater(route_url, params=["foo", "bar"])

        assert templater.route_template("foo") == "/:foo/:bar"

    def test_parameter_substrings(self):
        def route_url(_, **kwargs):
            return f"/api/{kwargs['id']}/things/{kwargs['thing_id']}"

        templater = AngularRouteTemplater(route_url, params=["id", "thing_id"])

        assert templater.route_template("foo") == "/api/:id/things/:thing_id"
