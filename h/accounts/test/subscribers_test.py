from mock import MagicMock
from pytest import fixture

from pyramid import testing

from ..events import LoginEvent
from ..subscribers import login


def test_login_subscriber(authn_policy):
    request = testing.DummyRequest(domain='example.com')
    user = DummyUser('joe.bloggs')

    event = LoginEvent(request, user)

    login(event)

    authn_policy.remember.assert_called_with(request,
                                             'acct:joe.bloggs@example.com')


class DummyUser(object):
    def __init__(self, username):
        self.username = username


class DummyAuthorizationPolicy(object):
    def permits(self, *args, **kwargs):
        return True


@fixture()
def authn_policy(config):
    authn_policy = MagicMock()
    config.set_authorization_policy(DummyAuthorizationPolicy())
    config.set_authentication_policy(authn_policy)
    return authn_policy
