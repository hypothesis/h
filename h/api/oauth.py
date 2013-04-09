from pyramid.httpexceptions import HTTPBadRequest

from h import messages


def access_token(request):
    """OAuth2 access token provider"""
    for name in [
        'client_id',
        'client_secret',
        'code',
        'state'
    ]:
        if name not in request.params:
            msg = '%s "%s".' % (messages.MISSING_PARAMETER, name)
            raise HTTPBadRequest(msg)

    raise NotImplementedError('OAuth provider not implemented yet.')
