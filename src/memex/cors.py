# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPBadRequest


def policy(allow_credentials=False,
           allow_headers=None,
           allow_methods=None,
           expose_headers=None,
           max_age=86400):
    """
    View decorator that provides CORS support.

    CORS stands for "Cross-Origin Resource Sharing," and is a protocol
    implemented in browsers to allow safe dispatch of XMLHttpRequests across
    origins.
    """

    def cors_decorator(wrapped):
        def wrapper(context, request):
            response = wrapped(context, request)
            return set_cors_headers(request, response,
                                    allow_credentials=allow_credentials,
                                    allow_headers=allow_headers,
                                    allow_methods=allow_methods,
                                    expose_headers=expose_headers,
                                    max_age=max_age)

        return wrapper

    return cors_decorator


def set_cors_headers(request, response,
                     allow_credentials=False,
                     allow_headers=None,
                     allow_methods=None,
                     expose_headers=None,
                     max_age=86400):
    # If the request is anything other than an OPTIONS request, we just
    # pass it through and add "A-C-A-O: *" to the response headers.
    if request.method != 'OPTIONS':
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    # Otherwise, we're dealing with a CORS preflight request, which,
    # according to the spec:
    #
    #  http://www.w3.org/TR/cors/#resource-preflight-requests
    #
    # ...MUST have an Origin header.
    origin = request.headers.get('Origin')
    if origin is None:
        raise HTTPBadRequest('CORS preflight request lacks Origin header.')

    # ...MUST have an Access-Control-Request-Method header.
    request_method = request.headers.get('Access-Control-Request-Method')
    if request_method is None:
        raise HTTPBadRequest('CORS preflight request lacks '
                             'Access-Control-Request-Method header.')

    # Always explicitly allow OPTIONS requests.
    methods = set(['OPTIONS'])
    if allow_methods is not None:
        methods.update(allow_methods)

    # We *could* verify that the preflight Access-Control-Request-Headers and
    # Access-Control-Request-Method match up with the allowed headers and
    # methods, but there's no need to do this as we can simply return what is
    # allowed and the browser will do the rest.
    headers = response.headers
    headers['Access-Control-Allow-Origin'] = origin
    headers['Access-Control-Allow-Methods'] = ', '.join(methods)
    headers['Access-Control-Max-Age'] = str(max_age)

    if allow_credentials:
        headers['Access-Control-Allow-Credentials'] = 'true'

    if allow_headers is not None:
        headers['Access-Control-Allow-Headers'] = ', '.join(allow_headers)

    if expose_headers is not None:
        headers['Access-Control-Expose-Headers'] = ', '.join(expose_headers)

    return response
