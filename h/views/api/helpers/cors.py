from pyramid.httpexceptions import HTTPBadRequest
from pyramid.response import Response


def policy(
    allow_credentials=False,
    allow_headers=None,
    allow_methods=None,
    expose_headers=None,
    max_age=86400,
):
    """
    View decorator factory that provides CORS support.

    CORS stands for "Cross-Origin Resource Sharing," and is a protocol
    implemented in browsers to allow safe dispatch of XMLHttpRequests across
    origins.

    To CORS-enable a view:

     1. Create a decorator using this function and set it as the view's
        decorator when calling `add_view`.
     2. To support requests that do not qualify as "simple requests" [1], add a
        preflight view using `add_preflight_view`.

    [1] https://developer.mozilla.org/en-US/docs/Web/HTTP/Access_control_CORS#Simple_requests
    """

    def cors_decorator(wrapped):
        def wrapper(context, request):
            response = wrapped(context, request)
            return set_cors_headers(
                request,
                response,
                allow_credentials=allow_credentials,
                allow_headers=allow_headers,
                allow_methods=allow_methods,
                expose_headers=expose_headers,
                max_age=max_age,
            )

        return wrapper

    return cors_decorator


def set_cors_headers(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    request,
    response,
    allow_credentials=False,
    allow_headers=None,
    allow_methods=None,
    expose_headers=None,
    max_age=86400,
):
    # If the request is anything other than an OPTIONS request, we just
    # pass it through and add "A-C-A-O: *" to the response headers.
    if request.method != "OPTIONS":
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    def raise_bad_request(missing_header):
        if request.exception:
            # Don't raise an exception if Pyramid is already processing an
            # exception view, because that will cause Pyramid to crash.
            return response
        raise HTTPBadRequest(f"CORS preflight request lacks {missing_header} header.")

    # Otherwise, we're dealing with a CORS preflight request, which,
    # according to the spec:
    #
    #  http://www.w3.org/TR/cors/#resource-preflight-requests
    #
    # ...MUST have an Origin header.
    origin = request.headers.get("Origin")
    if origin is None:
        return raise_bad_request("Origin")

    # ...MUST have an Access-Control-Request-Method header.
    request_method = request.headers.get("Access-Control-Request-Method")
    if request_method is None:
        return raise_bad_request("Access-Control-Request-Method")

    # Always explicitly allow OPTIONS requests.
    methods = {"OPTIONS"}
    if allow_methods is not None:
        methods.update(allow_methods)

    # We *could* verify that the preflight Access-Control-Request-Headers and
    # Access-Control-Request-Method match up with the allowed headers and
    # methods, but there's no need to do this as we can simply return what is
    # allowed and the browser will do the rest.
    headers = response.headers
    headers["Access-Control-Allow-Origin"] = origin
    headers["Access-Control-Allow-Methods"] = ", ".join(methods)
    headers["Access-Control-Max-Age"] = str(max_age)

    if allow_credentials:
        headers["Access-Control-Allow-Credentials"] = "true"

    if allow_headers is not None:
        headers["Access-Control-Allow-Headers"] = ", ".join(allow_headers)

    if expose_headers is not None:
        headers["Access-Control-Expose-Headers"] = ", ".join(expose_headers)

    return response


def add_preflight_view(config, route_name, cors_policy):
    """
    Add a view to handle CORS preflight requests for a given route.

    :param route_name: The route
    :param cors_policy: CORS policy created via a call to `policy`.
    """
    # Keep track of which routes already have preflight views registered.
    #
    # For a given route there may be multiple views with different predicates
    # (eg. to handle authenticated vs unauthenticated users). However we only
    # want one preflight view.
    if not hasattr(config.registry, "cors_preflighted_views"):
        config.registry.cors_preflighted_views = set()

    if route_name in config.registry.cors_preflighted_views:
        return

    def preflight_view(_context, _request):
        return Response()

    config.add_view(
        preflight_view,
        decorator=cors_policy,
        route_name=route_name,
        request_method="OPTIONS",
    )
    config.registry.cors_preflighted_views.add(route_name)
