# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyramid.view import forbidden_view_config
from pyramid.view import notfound_view_config
from pyramid.view import view_config
from ws4py.exc import HandshakeError
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from h.streamer import streamer, websocket


@view_config(route_name="ws")
def websocket_view(request):
    # Provide environment which the WebSocket handler can use...
    request.environ.update(
        {
            "h.ws.authenticated_userid": request.authenticated_userid,
            "h.ws.effective_principals": request.effective_principals,
            "h.ws.registry": request.registry,
            "h.ws.streamer_work_queue": streamer.WORK_QUEUE,
        }
    )

    # ...and ensure that any persistent connections associated with this
    # WebSocket connection are closed.
    request.db.close()

    app = WebSocketWSGIApplication(handler_cls=websocket.WebSocket)
    return request.get_response(app)


@notfound_view_config(renderer="json")
def notfound(exc, request):
    request.response.status_code = 404
    request.stats.incr("streamer.error.not_found")
    return {
        "ok": False,
        "error": "not_found",
        "reason": "These are not the droids you are looking for.",
    }


@forbidden_view_config(renderer="json")
def forbidden(exc, request):
    request.response.status_code = 403
    request.stats.incr("streamer.error.forbidden")
    return {
        "ok": False,
        "error": "forbidden",
        "reason": "You are not allowed here. Are you connecting from an "
        "allowed origin?",
    }


@view_config(context=HandshakeError, renderer="json")
def error_badhandshake(exc, request):
    request.response.status_code = 400
    request.stats.incr("streamer.error.bad_handshake")
    return {
        "ok": False,
        "error": "bad_handshake",
        "reason": "Handshake failed. Are you a WebSocket client?",
    }


@view_config(context=Exception, renderer="json")
def error(context, request):
    request.response.status_code = 500
    request.stats.incr("streamer.error.server_error")
    if request.debug:
        raise
    return {
        "ok": False,
        "error": "server_error",
        "reason": "An unexpected error occurred and has been reported.",
    }


def includeme(config):
    config.scan(__name__)
