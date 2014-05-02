# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from pyramid.renderers import get_renderer
from pyramid.settings import asbool

from h import events


@subscriber(events.BeforeRender)
def add_renderer_globals(event):
    request = event['request']

    # Set the base url to use in the <base> tag
    if hasattr(request, 'root'):
        event['base_url'] = request.resource_url(request.root, 'app')

    # Set the service url to use for API discovery
    event['service_url'] = request.route_url('api', subpath='')

    # Set the blocks property to refer to the block helpers template
    event['blocks'] = get_renderer('templates/blocks.pt').implementation()


@subscriber(events.NewRequest, asset_request=False)
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
@subscriber(events.NewRegistrationEvent, autologin=True)
@subscriber(events.PasswordResetEvent, autologin=True)
@subscriber(events.RegistrationActivatedEvent)
def login(event):
    request = event.request
    user = event.user
    request.user = user


@subscriber(events.LogoutEvent)
def logout(event):
    request = event.request
    request.user = None


class AutoLogin(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, val, config):
        self.env = config.get_webassets_env()
        self.val = val

    def text(self):
        return 'autologin = %s' % (self.val,)

    phash = text

    def __call__(self, event):
        request = event.request
        settings = request.registry.settings
        autologin = asbool(settings.get('horus.autologin', False))
        return self.val == autologin


def includeme(config):
    config.add_subscriber_predicate('autologin', AutoLogin)
    config.scan(__name__)
