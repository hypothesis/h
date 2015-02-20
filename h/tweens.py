# -*- coding: utf-8 -*-
def annotator_tween_factory(handler, registry):
    """A tween that copies the value of the Annotator token header into the
    the HTTP Authorization header with the Bearer token type.
    """

    def annotator_tween(request):
        token = request.headers.get('X-Annotator-Auth-Token')
        if token is not None:
            request.authorization = ('Bearer', token)
        return handler(request)

    return annotator_tween
