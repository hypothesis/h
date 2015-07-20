# -*- coding: utf-8 -*-
def auth_token(handler, registry):
    """
    A tween that copies the value of the Annotator token header into the the
    HTTP Authorization header with the Bearer token type.
    """

    def tween(request):
        token = request.headers.get('X-Annotator-Auth-Token')
        if token is not None:
            request.authorization = ('Bearer', token)
        return handler(request)

    return tween


def csrf_tween_factory(handler, registry):
    """A tween that sets a 'XSRF-TOKEN' cookie."""

    def csrf_tween(request):
        response = handler(request)

        # NB: the session does not necessarily supply __len__.
        session_is_empty = len(request.session.keys()) == 0

        # Ignore an empty session.
        if request.session.new and session_is_empty:
            return response

        csrft = request.session.get_csrf_token()

        if request.cookies.get('XSRF-TOKEN') != csrft:
            response.set_cookie('XSRF-TOKEN', csrft)

        return response

    return csrf_tween
