# -*- coding: utf-8 -*-
import pytest

from mock import ANY, MagicMock, patch, Mock
from pyramid import testing
import unittest

import jwt

from h import auth, interfaces

KEY = 'someclient'
SECRET = 'somesecret'


class MockClient(object):
    def __init__(self, request, client_id):
        self.client_id = client_id
        self.client_secret = SECRET if client_id is KEY else None


class TestRequestValidator(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.security = testing.DummySecurityPolicy()
        self.config.set_authorization_policy(self.security)
        self.config.set_authentication_policy(self.security)
        self.client_patcher = patch('h.auth.get_client')
        self.client = self.client_patcher.start()
        self.decode_patcher = patch('jwt.decode')
        self.decode = self.decode_patcher.start()
        self.request = testing.DummyRequest(client=None, user=None)
        self.validator = auth.RequestValidator()
        self.request.registry.settings['h.client_id'] = KEY
        self.request.registry.settings['h.client_secret'] = SECRET

    def tearDown(self):
        testing.tearDown()
        self.client_patcher.stop()
        self.decode_patcher.stop()

    def test_authenticate_client_ok(self):
        client = MockClient(self.request, KEY)
        self.request.client_id = KEY
        self.request.client_secret = SECRET
        self.client.return_value = client
        res = self.validator.authenticate_client(self.request)
        assert res is True
        assert self.request.client is client
        assert self.request.user is None

    def test_authenticate_client_not_ok(self):
        self.request.client_id = KEY
        self.request.client_secret = SECRET
        self.client.return_value = None
        res = self.validator.authenticate_client(self.request)
        assert self.client.called
        assert res is False
        assert self.request.client is None
        assert self.request.user is None

    def test_authenticate_client_csrf_ok(self):
        client = MockClient(self.request, KEY)
        self.security.userid = 'hooper'
        self.request.client_id = None
        self.request.client_secret = None
        self.client.return_value = client
        with patch('pyramid.session.check_csrf_token') as csrf:
            csrf.return_value = True
            res = self.validator.authenticate_client(self.request)
        assert res is True
        assert self.request.client is client
        assert self.request.user == 'hooper'

    def test_authenticate_client_csrf_not_ok(self):
        self.request.client_id = None
        self.request.client_secret = None
        res = self.validator.authenticate_client(self.request)
        assert res is False
        assert self.request.client is None
        assert self.request.user is None

    def test_validate_bearer_token_client_invalid(self):
        self.client.return_value = None
        self.decode.return_value = {'iss': 'fake-client'}
        res = self.validator.validate_bearer_token('', None, self.request)
        assert res is False
        self.client.assert_called_once_with(self.request, 'fake-client')

    def test_validate_bearer_token_format_invalid(self):
        self.decode.side_effect = jwt.InvalidTokenError
        res = self.validator.validate_bearer_token('', None, self.request)
        assert res is False

    def test_validate_bearer_token_signature_invalid(self):
        client = MockClient(self.request, KEY)
        self.client.return_value = client
        self.decode.return_value = {'iss': KEY}
        self.decode.side_effect = jwt.InvalidTokenError
        res = self.validator.validate_bearer_token('', [], self.request)

        expected = [
            ('', {'verify': False}),
            ('', {'key': SECRET, 'audience': self.request.host_url,
                  'leeway': ANY, 'algorithms': ['HS256']})
        ]

        self.decode.call_args_list == expected

        assert res is False

    def test_validate_bearer_token_valid(self):
        client = MockClient(self.request, KEY)
        self.client.return_value = client
        self.decode.return_value = {'iss': KEY, 'sub': 'citizen'}
        res = self.validator.validate_bearer_token('', None, self.request)
        assert res is True
        assert self.request.client is client
        assert self.request.user == 'citizen'


def test_get_client(config):
    client = MockClient(None, '4321')
    mock_factory = MagicMock()
    mock_factory.return_value = client
    registry = config.registry
    registry.registerUtility(mock_factory, interfaces.IClientFactory)
    request = testing.DummyRequest(registry=config.registry)
    assert auth.get_client(request, '4321') is client
    mock_factory.assert_called_with(request, '4321')


def test_get_client_missing(config):
    mock_factory = MagicMock()
    mock_factory.return_value = None
    registry = config.registry
    registry.registerUtility(mock_factory, interfaces.IClientFactory)
    request = testing.DummyRequest(registry=config.registry)
    assert auth.get_client(request, '9876') is None
    mock_factory.assert_called_with(request, '9876')


def test_get_client_bad_secret(config):
    client = MockClient(None, '9876')
    client.client_secret = 'scramble'
    mock_factory = MagicMock()
    mock_factory.return_value = client
    registry = config.registry
    registry.registerUtility(mock_factory, interfaces.IClientFactory)
    request = testing.DummyRequest(registry=config.registry)
    assert auth.get_client(request, '9876', client_secret='1234') is None
    mock_factory.assert_called_with(request, '9876')


# The fixtures required to mock all of effective_principals()'s dependencies.
effective_principals_fixtures = pytest.mark.usefixtures('models', 'groups')


@effective_principals_fixtures
def test_effective_principals_returns_no_principals(models):
    """It should return only [] by default.

    If the request has no client and the user is not an admin or staff member
    nor a member of any group, it should return no additional principals.

    """
    request = MagicMock(client=None)
    models.User.get_by_userid.return_value = MagicMock(
        admin=False, staff=False)

    assert auth.effective_principals("jiji", request) == []


@effective_principals_fixtures
def test_effective_principals_returns_client_id_as_consumer(models):
    """
    If the request has a client ID it's returned as a "consumer:" principal.
    """
    request = MagicMock(client=MagicMock(client_id="test_id"))
    models.User.get_by_userid.return_value = MagicMock(
        admin=False, staff=False)

    assert "consumer:test_id" in auth.effective_principals("jiji", request)


@effective_principals_fixtures
def test_effective_principals_with_admin_user(models):
    """If the user is an admin it should return "group:__admin__"."""
    request = MagicMock(client=None)
    models.User.get_by_userid.return_value = MagicMock(admin=True, staff=False)

    assert "group:__admin__" in auth.effective_principals("jiji", request)


@effective_principals_fixtures
def test_effective_principals_client_id_and_admin_together(models):
    request = MagicMock(client=MagicMock(client_id="test_id"))
    models.User.get_by_userid.return_value = MagicMock(admin=True, staff=False)

    principals = auth.effective_principals("jiji", request)
    assert "consumer:test_id" in principals
    assert "group:__admin__" in principals


@effective_principals_fixtures
def test_effective_principals_with_staff_user(models):
    """If the user is staff it should return a "group:__staff__" principal."""
    request = MagicMock(client=None)
    models.User.get_by_userid.return_value = MagicMock(admin=False, staff=True)

    assert "group:__staff__" in auth.effective_principals("jiji", request)


@effective_principals_fixtures
def test_effective_principals_client_id_and_admin_and_staff(models):
    request = MagicMock(client=MagicMock(client_id="test_id"))
    models.User.get_by_userid.return_value = MagicMock(admin=True, staff=True)

    principals = auth.effective_principals("jiji", request)

    assert "consumer:test_id" in principals
    assert "group:__admin__" in principals
    assert "group:__staff__" in principals


@effective_principals_fixtures
def test_effective_principals_calls_group_principals(models, groups):
    request = Mock()

    auth.effective_principals("jiji", request)

    groups.group_principals.assert_called_once_with(
        models.User.get_by_userid.return_value, "jiji", request.hashids)


@effective_principals_fixtures
def test_effective_principals_with_one_group(groups):
    groups.group_principals.return_value = ['group:group-1']

    additional_principals = auth.effective_principals("jiji", Mock())

    assert 'group:group-1' in additional_principals


@effective_principals_fixtures
def test_effective_principals_with_three_groups(groups):
    groups.group_principals.return_value = [
        'group:group-1',
        'group:group-2',
        'group:group-3'
    ]

    additional_principals = auth.effective_principals("jiji", Mock())

    assert 'group:group-1' in additional_principals
    assert 'group:group-2' in additional_principals
    assert 'group:group-3' in additional_principals


@pytest.fixture
def models(request):
    patcher = patch('h.auth.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def groups(request):
    patcher = patch('h.auth.groups', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
