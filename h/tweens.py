# -*- coding: utf-8 -*-


def csrf_tween_factory(handler, registry):
    """A tween that sets a 'XSRF-TOKEN' cookie."""

    def csrf_tween(request):
        response = handler(request)
        csrft = request.session.get_csrf_token()
        if request.cookies.get('XSRF-TOKEN') != csrft:
            response.set_cookie('XSRF-TOKEN', csrft)
        return response

    return csrf_tween
