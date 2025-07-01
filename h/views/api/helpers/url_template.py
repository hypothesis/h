import re

from pyramid.interfaces import IRoutesMapper


class RouteNotFoundError(Exception):
    def __init__(self, route_name: str):
        super().__init__(f"Route '{route_name}' not found")
        self.route_name = route_name


def route_url_template(request, route_name: str) -> str:
    """
    Return a URL template for a Pyramid route.

    URL templates have the format "https://example.com/users/:username" where
    ":username" is a dynamic parameter.
    """

    # Route lookup code taken from `request.route_url` implementation.
    routes = request.registry.getUtility(IRoutesMapper)
    route = routes.get_route(route_name)

    if route is None:
        raise RouteNotFoundError(route_name)

    # Route patterns are strings like "/users/{username}/items/{item}". Extract
    # the names of the dynamic parts.
    #
    # The dynamic parts can contain character set restrictions and also lengths,
    # resulting in patterns like "/api/annotations/{id:[A-Za-z0-9_-]{20,22}}"
    # which can't be parsed with a regex. These more complex cases are handled
    # below by catching the `KeyError` and retrying.
    param_names = re.findall(r"\{([A-Za-z0-9_.]+)\}", route.pattern)

    def placeholder(name):
        # nb. This assumes that the parameter name contains only URL-safe
        # characters which will not be affected by URL encoding.
        return f":{name}"

    params = {name: placeholder(name) for name in param_names}

    while True:
        try:
            return request.route_url(route_name, **params)
        except KeyError as exc:
            param = exc.args[0]
            params[param] = placeholder(param)
