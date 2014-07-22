# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from pyramid.renderers import get_renderer

from h import events


@subscriber(events.BeforeRender)
def add_renderer_globals(event):
    request = event['request']

    # Set the base url to use in the <base> tag
    if hasattr(request, 'root'):
        event['base_url'] = request.resource_url(request.root, '')

    # Set the service url to use for API discovery
    event['service_url'] = request.route_url('api', subpath='')

    # Set the blocks property to refer to the block helpers template
    event['blocks'] = get_renderer('h:templates/blocks.pt').implementation()


@subscriber(events.NewRequest, asset_request=False)
@subscriber(events.LogoutEvent)
def ensure_csrf(event):
    event.request.session.get_csrf_token()


@subscriber(events.NewResponse, asset_request=False)
def set_csrf_cookie(event):
    request = event.request
    response = event.response
    session = request.session

    if len(session) == 0:
        response.set_cookie('XSRF-TOKEN', None)
    else:
        token = session.get_csrf_token()
        if request.cookies.get('XSRF-TOKEN') != token:
            response.set_cookie('XSRF-TOKEN', token)


@subscriber(events.LoginEvent)
def login(event):
    request = event.request
    user = event.user
    session = request.session

    personas = session.setdefault('personas', [])

    if user not in personas:
        personas.append(user)
        session.changed()


@subscriber(events.LogoutEvent)
def logout(event):
    event.request.session.invalidate()


def includeme(config):
    config.scan(__name__)
