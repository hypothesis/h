# -*- coding: utf-8 -*-
from horus.events import (
    NewRegistrationEvent,
    RegistrationActivatedEvent,
    PasswordResetEvent,
    ProfileUpdatedEvent,
)
from pyramid.events import (
    BeforeRender,
    NewResponse,
)

__all__ = [
    'NewRegistrationEvent',
    'RegistrationActivatedEvent',
    'PasswordResetEvent',
    'ProfileUpdatedEvent',
    'BeforeRender',
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
