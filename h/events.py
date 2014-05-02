# -*- coding: utf-8 -*-
from horus.events import (
    NewRegistrationEvent,
    RegistrationActivatedEvent,
    PasswordResetEvent,
    ProfileUpdatedEvent,
)
from pyramid.events import BeforeRender, NewRequest, NewResponse

__all__ = [
    'LoginEvent',
    'LogoutEvent',
    'NewRegistrationEvent',
    'RegistrationActivatedEvent',
    'PasswordResetEvent',
    'ProfileUpdatedEvent',
    'BeforeRender',
    'NewRequest',
    'NewResponse',
]


class AnnotationEvent(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, request, annotation, action):
        self.request = request
        self.annotation = annotation
        self.action = action


class LoginEvent(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, request, user):
        self.request = request
        self.user = user


class LogoutEvent(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, request):
        self.request = request
