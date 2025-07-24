class UnexpectedRouteError(Exception):
    """An unexpected Pyramid route name was received.

    Sometimes it's useful for view code to read request.matched_route.name, for
    example when a single view callable handles multiple routes and wants to
    vary something based on the route. The code can raise UnexpectedRouteError
    if it receives a route name that it wasn't expecting:

        match request.matched_route.name:
            case "foo":
                do_something()
            case "bar":
                do_something_else()
            case _:
                raise UnexpectedRouteError(request.matched_route.name)

    """

    def __init__(self, route_name):
        super().__init__(route_name)
