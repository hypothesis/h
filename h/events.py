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


class AnnotatorStoreEvent(object):
    def __init__(self, annotation, action):
        self.annotation = annotation
        self.action = action
