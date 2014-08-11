from pyramid.events import NewRequest, subscriber
from pyramid.settings import asbool
from horus.events import (
    NewRegistrationEvent,
    RegistrationActivatedEvent,
    PasswordResetEvent,
)


@subscriber(NewRequest, asset_request=False)
def ensure_csrf(event):
    event.request.session.get_csrf_token()


@subscriber(NewRegistrationEvent, autologin=True)
@subscriber(PasswordResetEvent, autologin=True)
@subscriber(RegistrationActivatedEvent)
def login(event):
    request = event.request
    request.user = event.user


class AutoLogin(object):
    # pylint: disable=too-few-public-methods

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
