# -*- coding: utf-8 -*-
from pyramid import httpexceptions as exc
from pyramid.view import view_config

from h.notification.models import Subscriptions


@view_config(route_name='unsubscribe', renderer='h:templates/unsubscribe.html')
def unsubscribe(request):
    if not request.feature('notification'):
        raise exc.HTTPNotFound()

    token = request.matchdict['token']
    payload = request.registry.notification_serializer.loads(token)

    subscriptions = Subscriptions.get_templates_for_uri_and_type(
        payload['uri'],
        payload['type'])

    for s in subscriptions:
        if s.active:
            s.active = False
            request.db.add(s)

    return {}


def includeme(config):
    config.add_route('unsubscribe', '/notification/unsubscribe/{token}')
    config.scan(__name__)
