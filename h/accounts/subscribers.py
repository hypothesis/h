# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.events import subscriber

from h.accounts import events


@subscriber(events.LoginEvent)
def login(event):
    event.request.stats.incr("auth.local.login")


@subscriber(events.LogoutEvent)
def logout(event):
    event.request.stats.incr("auth.local.logout")


@subscriber(events.PasswordResetEvent)
def password_reset(event):
    event.request.stats.incr("auth.local.reset_password")


@subscriber(events.ActivationEvent)
def activation(event):
    event.request.stats.incr("auth.local.activate")


def includeme(config):
    config.scan(__name__)
