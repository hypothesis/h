# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from h.models import Subscriptions


@view_config(route_name='unsubscribe',
             renderer='h:templates/unsubscribe.html.jinja2')
def unsubscribe(request):
    token = request.matchdict['token']
    try:
        payload = request.registry.notification_serializer.loads(token)
    except ValueError:
        raise HTTPNotFound()

    subscriptions = request.db.query(Subscriptions).filter_by(type=payload['type'],
                                                              uri=payload['uri'])

    for s in subscriptions:
        if s.active:
            s.active = False

    return {}


def includeme(config):
    config.add_route('unsubscribe', '/notification/unsubscribe/{token}')
    config.scan(__name__)
