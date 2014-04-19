# -*- coding: utf-8 -*-
from pyramid.events import subscriber, BeforeRender
from pyramid.renderers import get_renderer
from pyramid.settings import asbool

from h import events


@subscriber(BeforeRender)
def add_render_view_global(event):
    event['blocks'] = get_renderer('templates/blocks.pt').implementation()


@subscriber(events.NewRegistrationEvent)
@subscriber(events.RegistrationActivatedEvent)
def registration(event):
    request = event.request
    settings = request.registry.settings
    autologin = asbool(settings.get('horus.autologin', False))

    if isinstance(event, events.RegistrationActivatedEvent) or autologin:
        request.user = event.user


def includeme(config):
    config.scan(__name__)
