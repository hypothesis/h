from pyramid.view import forbidden_view_config, notfound_view_config, view_config
from ws4py.exc import HandshakeError
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from h.streamer import streamer, websocket


@view_config(route_name="ws")
def websocket_view(request):
    # Provide environment which the WebSocket handler can use...
    request.environ.update(
        {
            "h.ws.streamer_work_queue": streamer.WORK_QUEUE,
            "h.ws.identity": request.identity,
        }
    )

    app = WebSocketWSGIApplication(handler_cls=websocket.WebSocket)
    return request.get_response(app)


@notfound_view_config(renderer="json")
def notfound(_exc, request):
    request.response.status_code = 404
    return {
        "ok": False,
        "error": "not_found",
        "reason": "These are not the droids you are looking for.",
    }


@forbidden_view_config(renderer="json")
def forbidden(_exc, request):
    request.response.status_code = 403
    return {
        "ok": False,
        "error": "forbidden",
        "reason": "You are not allowed here. Are you connecting from an "
        "allowed origin?",
    }


@view_config(context=HandshakeError, renderer="json")
def error_badhandshake(_exc, request):
    request.response.status_code = 400
    return {
        "ok": False,
        "error": "bad_handshake",
        "reason": "Handshake failed. Are you a WebSocket client?",
    }


@view_config(context=Exception, renderer="json")
def error(_context, request):
    request.response.status_code = 500

    return {
        "ok": False,
        "error": "server_error",
        "reason": "An unexpected error occurred and has been reported.",
    }
