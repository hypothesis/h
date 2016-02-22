# -*- coding: utf-8 -*-

from pyramid.config import aslist
from pyramid.httpexceptions import HTTPBadRequest, HTTPForbidden
from ws4py.exc import HandshakeError
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from h.streamer import websocket


def websocket_view(request):
    # WebSockets can be opened across origins and send cookies. To prevent
    # scripts on other sites from using this socket, ensure that the Origin
    # header (if present) matches the request host URL or is whitelisted.
    origin = request.headers.get('Origin')
    allowed = aslist(request.registry.settings.get('origins', ''))
    if origin is not None:
        if origin != request.host_url and origin not in allowed:
            return HTTPForbidden()
    app = WebSocketWSGIApplication(handler_cls=websocket.WebSocket)
    return request.get_response(app)


def bad_handshake(exc, request):
    return HTTPBadRequest()


def includeme(config):
    config.add_route('ws', 'ws')
    config.add_view(websocket_view, route_name='ws')
    config.add_view(bad_handshake, context=HandshakeError)
    config.scan(__name__)
