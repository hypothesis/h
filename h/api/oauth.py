from pyramid.httpexceptions import HTTPBadRequest

from h.models import _


def access_token(request):
    """OAuth2 access token provider"""
    for name in [
        'client_id',
        'client_secret',
        'code',
        'state'
    ]:
        if name not in request.params:
            msg = _('Missing parameter "${name}".', mapping={'name': name})
            raise HTTPBadRequest(msg)

    raise NotImplementedError('OAuth provider not implemented yet.')
