from webob import Response
from webob.dec import wsgify
from webob.exc import HTTPBadRequest


@wsgify.middleware
def permit_cors(req,
                app,
                allow_credentials=False,
                allow_headers=None,
                allow_methods=None,
                expose_headers=None,
                max_age=86400):
    """
    WSGI middleware that enables CORS support across an application.

    CORS stands for "Cross-Origin Resource Sharing," and is a protocol
    implemented in browsers to allow safe dispatch of XMLHttpRequests across
    origins.
    """
    # If the request is anything other than an OPTIONS request, we just
    # pass it through and add "A-C-A-O: *" to the response headers.
    if req.method != 'OPTIONS':
        resp = req.get_response(app)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    # Otherwise, we're dealing with a CORS preflight request, which,
    # according to the spec:
    #
    #  http://www.w3.org/TR/cors/#resource-preflight-requests
    #
    # ...MUST have an Origin header.
    origin = req.headers.get('Origin')
    if origin is None:
        raise HTTPBadRequest('CORS preflight request lacks Origin header.')

    # ...MUST have an Access-Control-Request-Method header.
    request_method = req.headers.get('Access-Control-Request-Method')
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
    resp = Response()
    headers = resp.headers
    headers['Access-Control-Allow-Origin'] = origin
    headers['Access-Control-Allow-Methods'] = ', '.join(methods)
    headers['Access-Control-Max-Age'] = str(max_age)

    if allow_credentials:
        headers['Access-Control-Allow-Credentials'] = 'true'

    if allow_headers is not None:
        headers['Access-Control-Allow-Headers'] = ', '.join(allow_headers)

    if expose_headers is not None:
        headers['Access-Control-Expose-Headers'] = ', '.join(expose_headers)

    return resp

