# -*- coding: utf-8 -*-
from pyramid.events import subscriber
from pyramid.settings import asbool

from horus.events import (
    NewRegistrationEvent,
    RegistrationActivatedEvent,
    PasswordResetEvent,
)

from h.stats import get_client as stats


@subscriber(RegistrationActivatedEvent)
def activate(event):
    stats(event.request).get_counter('auth.local.activate').increment()


@subscriber(NewRegistrationEvent, autologin=True)
@subscriber(PasswordResetEvent, autologin=True)
@subscriber(RegistrationActivatedEvent)
def login(event):
    request = event.request
    user = event.user
    request.user = user


class AutoLogin(object):

    def __init__(self, val, config):
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
