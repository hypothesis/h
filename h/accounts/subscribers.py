# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pyramid.events import subscriber

from h.accounts import events
from h.stats import get_client as stats


@subscriber(events.LoginEvent)
def login(event):
    stats(event.request).get_counter('auth.local.login').increment()


@subscriber(events.LogoutEvent)
def logout(event):
    stats(event.request).get_counter('auth.local.logout').increment()


@subscriber(events.RegistrationEvent)
def registration(event):
    stats(event.request).get_counter('auth.local.register').increment()


@subscriber(events.PasswordResetEvent)
def password_reset(event):
    stats(event.request).get_counter('auth.local.reset_password').increment()


@subscriber(events.ActivationEvent)
def activation(event):
    stats(event.request).get_counter('auth.local.activate').increment()


def includeme(config):
    config.scan(__name__)
