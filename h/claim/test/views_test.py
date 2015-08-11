# pylint: disable=no-self-use
import mock
import pytest

import deform
from pytest import raises
from pyramid.testing import DummyRequest as _DummyRequest
from pyramid.httpexceptions import HTTPFound, HTTPNotFound

from h.conftest import DummyFeature

from ..views import claim_account
from ..views import update_account


class DummyRequest(_DummyRequest):
    def __init__(self, *args, **kwargs):
        params = {
            # Add a dummy feature flag querier to the request
            'feature': DummyFeature(),
        }
        params.update(kwargs)
        super(DummyRequest, self).__init__(*args, **params)


def test_claim_account_returns_form():
    request = _get_request()

    res = claim_account(request)
    assert 'form' in res


def test_claim_account_missing_token_404s():
    request = _get_request()
    del request.matchdict['token']

    with raises(HTTPNotFound):
        claim_account(request)


def test_claim_account_invalid_token_404s():
    serializer = mock.Mock(spec=FakeSerializer())
    serializer.loads.side_effect = ValueError("Boom!")

    request = _get_request()
    request.registry.claim_serializer = serializer

    with raises(HTTPNotFound):
        claim_account(request)


def test_claim_account_valid_token_unknown_user_404s(user_model):
    user_model.get_by_userid.return_value = None

    request = _get_request()

    with raises(HTTPNotFound):
        claim_account(request)


def test_claim_account_signed_in_redirects(authn_policy):
    authn_policy.authenticated_userid.return_value = 'acct:billy@localhost'

    request = _get_request()

    with raises(HTTPFound) as exc:
        claim_account(request)

    assert exc.value.location == 'http://example.com/dummy/stream'


def test_claim_account_already_claimed_redirects(user_model):
    user_model.get_by_userid.return_value = FakeUser(password='alreadyset')

    request = _get_request()

    with raises(HTTPFound) as exc:
        claim_account(request)

    assert exc.value.location == 'http://example.com/dummy/stream'


def test_update_account_updates_password(user_model):
    user_model.get_by_userid.return_value = user = FakeUser(password='')

    request = _post_request(post={'password': 'donkeys'})

    update_account(request)

    assert user.password == 'donkeys'


def test_update_account_redirects_to_index(user_model):
    user_model.get_by_userid.return_value = FakeUser(password='')

    request = _post_request(post={'password': 'donkeys'})

    res = update_account(request)

    assert isinstance(res, HTTPFound)
    assert res.location == 'http://example.com/'


def test_update_account_rerenders_form_on_validation_error(form, user_model):
    request = _post_request(post={'password': 'giraffes'})
    request.registry.claim_serializer = FakeSerializer()
    form.return_value.validate.side_effect = deform.ValidationFailure(None,
                                                                      None,
                                                                      None)
    user_model.get_by_userid.return_value = FakeUser(password='')

    res = update_account(request)

    assert 'form' in res


def test_update_account_signed_in_redirects(authn_policy):
    authn_policy.authenticated_userid.return_value = 'acct:billy@localhost'

    request = _post_request()

    with raises(HTTPFound) as excinfo:
        update_account(request)

    assert excinfo.value.location == 'http://example.com/dummy/stream'


def test_update_account_already_claimed_redirects(user_model):
    user_model.get_by_userid.return_value = FakeUser(password='alreadyset')

    request = _post_request()

    with raises(HTTPFound) as exc:
        update_account(request)

    assert exc.value.location == 'http://example.com/dummy/stream'


def test_update_account_missing_token_not_found():
    request = _post_request()
    del request.matchdict['token']

    with raises(HTTPNotFound):
        update_account(request)


def test_update_account_invalid_token_not_found():
    serializer = mock.Mock(spec=FakeSerializer())
    serializer.loads.side_effect = ValueError("Boom!")

    request = _post_request()
    request.registry.claim_serializer = serializer

    with raises(HTTPNotFound):
        update_account(request)


def test_update_account_redirects_when_registered(user_model):
    request = _post_request()
    user_model.get_by_userid.return_value = FakeUser(password='alreadyset')

    with raises(HTTPFound) as excinfo:
        update_account(request)

    assert excinfo.value.location == 'http://example.com/dummy/stream'


class FakeUser(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])


class FakeSerializer(object):
    def dumps(self, obj):
        return 'faketoken'

    def loads(self, token):
        return {'userid': 'acct:foo@bar.com'}


def _get_request():
    request = DummyRequest()
    request.matchdict['token'] = 'testtoken'
    request.registry.claim_serializer = FakeSerializer()
    return request


def _post_request(post=None):
    if post is None:
        post = {}
    post.update({'csrf_token': 'testcsrftoken'})

    request = DummyRequest(post)
    request.matchdict['token'] = 'testtoken'
    request.registry.claim_serializer = FakeSerializer()

    request.session.get_csrf_token = lambda: 'testcsrftoken'

    return request


@pytest.fixture(autouse=True)
def routes(config):
    """Add routes used by claim package"""
    config.add_route('index', '/')
    config.add_route('stream', '/dummy/stream')


@pytest.fixture(autouse=True)
def user_model(request):
    patcher = mock.patch('h.claim.views.User', autospec=True)
    request.addfinalizer(patcher.stop)
    model = patcher.start()
    model.get_by_userid.return_value = FakeUser(password='')
    return model


@pytest.fixture
def form(request):
    patcher = mock.patch('h.claim.views.deform.Form', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
