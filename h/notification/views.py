# -*- coding: utf-8 -*-
from hem.db import get_session
from pyramid.view import view_config

from h.notification.models import Subscriptions


@view_config(route_name='unsubscribe', renderer='h:templates/unsubscribe.html')
def unsubscribe(request):
    token = request.matchdict['token']
    payload = request.registry.notification_serializer.loads(token)

    subscriptions = Subscriptions.get_templates_for_uri_and_type(
        request,
        payload['uri'],
        payload['type'],
    )

    db = get_session(request)
    for s in subscriptions:
        if s.active:
            s.active = False
            db.add(s)

    return {}


def includeme(config):
    config.add_route('unsubscribe', '/notification/unsubscribe/{token}')
    config.scan(__name__)
