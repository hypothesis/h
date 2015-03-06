# -*- coding: utf-8 -*-


def set_user_from_oauth(event):
    """A subscriber that checks requests for OAuth credentials and sets the
    'REMOTE_USER' environment key to the authorized user (or ``None``)."""
    request = event.request
    request.verify_request()
    request.environ['REMOTE_USER'] = getattr(request, 'user', None)
