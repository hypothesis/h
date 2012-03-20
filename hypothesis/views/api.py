from pyramid.response import Response
from pyramid.view import view_config, view_defaults

from annotator import auth

def cors_headers(request):
    ac = 'Access-Control-'
    headers = {}

    headers[ac + 'Allow-Origin']      = request.headers.get('origin', '*')
    headers[ac + 'Allow-Credentials'] = 'true'
    headers[ac + 'Expose-Headers']    = 'Location, Content-Type, Content-Length'

    if request.method == 'OPTIONS':
        headers[ac + 'Allow-Headers'] = 'X-Requested-With, Content-Type, Content-Length'
        headers[ac + 'Allow-Methods'] = 'GET, OPTIONS'
        headers[ac + 'Max-Age']       = '86400'

    return headers
    

@view_defaults(route_name='api_token')
class TokenView(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method='GET')
    def get(self):
        """
        if request.user:
            return jsonify(g.auth.generate_token('annotateit', g.user.username), headers=headers)
        else:
            return jsonify('Please go to {0} to log in!'.format(request.host_url), status=401, headers=headers)
        """

        payload = {'userId': 'bogus'}
        kwargs = {
            'headerlist': cors_headers(self.request).items(),
        }
        
        if self.request.user:
            kwargs['body'] = auth.encode_token(payload, 's33cr7t')
            kwargs['status'] = 200
        else:
            kwargs['body'] = "Please log in: %s" % request.application_url
            kwargs['status'] = 401

        return Response(**kwargs)

    @view_config(request_method='OPTIONS')
    def options(self):
        return Response(headerlist=cors_headers(self.request).items())
