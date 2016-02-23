# -*- coding: utf-8 -*-

from pyramid import httpexceptions
from pyramid.config import aslist
from ws4py.exc import HandshakeError
from ws4py.server.wsgiutils import WebSocketWSGIApplication

from h.streamer import websocket


def websocket_view(request):
    # WebSockets can be opened across origins and send cookies. To prevent
    # scripts on other sites from using this socket, ensure that the Origin
    # header (if present) matches the request host URL or is whitelisted.
    origin = request.headers.get('Origin')
    allowed = request.registry.settings['origins']
    if origin is not None:
        if origin != request.host_url and origin not in allowed:
            return httpexceptions.HTTPForbidden()
    app = WebSocketWSGIApplication(handler_cls=websocket.WebSocket)
    return request.get_response(app)


def bad_handshake(exc, request):
    raise httpexceptions.HTTPBadRequest()


def includeme(config):
    settings = config.registry.settings
    settings['origins'] = aslist(settings.get('origins', ''))
    config.add_view(websocket_view, route_name='ws')
    config.add_view(bad_handshake, context=HandshakeError)
