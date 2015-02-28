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
