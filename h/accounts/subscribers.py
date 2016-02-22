# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.events import subscriber

from h.accounts import events


@subscriber(events.LoginEvent)
def login(event):
    event.request.stats.get_counter('auth.local.login').increment()


@subscriber(events.LogoutEvent)
def logout(event):
    event.request.stats.get_counter('auth.local.logout').increment()


@subscriber(events.RegistrationEvent)
def registration(event):
    event.request.stats.get_counter('auth.local.register').increment()


@subscriber(events.PasswordResetEvent)
def password_reset(event):
    event.request.stats.get_counter('auth.local.reset_password').increment()


@subscriber(events.ActivationEvent)
def activation(event):
    event.request.stats.get_counter('auth.local.activate').increment()


def includeme(config):
    config.scan(__name__)
