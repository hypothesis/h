__all__ = [
    'NewRegistrationEvent',
    'RegistrationActivatedEvent',
    'PasswordResetEvent',
    'ProfileUpdatedEvent',
]

from horus.events import (
    NewRegistrationEvent,
    RegistrationActivatedEvent,
    PasswordResetEvent,
    ProfileUpdatedEvent,
)


class AnnotationEvent(object):
    def __init__(self, request, annotation, action):
        self.request = request
        self.annotation = annotation
        self.action = action
