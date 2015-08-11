# -*- coding: utf-8 -*-
from mock import ANY, MagicMock, patch
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
        self.client.assert_called()
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


@patch("h.auth.models.User.get_by_userid")
def test_effective_principals_returns_no_principals(get_by_userid):
    """It should return no principals if no client, admin or staff.

    If the request has no client and the user is not an admin or staff member,
    then it should return no principals.

    """
    request = MagicMock(client=None)
    get_by_userid.return_value = MagicMock(admin=False, staff=False)

    assert auth.effective_principals("jiji", request) == []


@patch("h.auth.models.User.get_by_userid")
def test_effective_principals_returns_client_id_as_consumer(get_by_userid):
    """
    If the request has a client ID it's returned as a "consumer:" principal.
    """
    request = MagicMock(client=MagicMock(client_id="test_id"))
    get_by_userid.return_value = MagicMock(admin=False, staff=False)

    assert auth.effective_principals("jiji", request) == ["consumer:test_id"]


@patch("h.auth.models.User.get_by_userid")
def test_effective_principals_with_admin_user(get_by_userid):
    """If the user is an admin it should return a "group:admin" principal."""
    request = MagicMock(client=None)
    get_by_userid.return_value = MagicMock(admin=True, staff=False)

    assert auth.effective_principals("jiji", request) == ["group:admin"]


@patch("h.auth.models.User.get_by_userid")
def test_effective_principals_client_id_and_admin_together(get_by_userid):
    request = MagicMock(client=MagicMock(client_id="test_id"))
    get_by_userid.return_value = MagicMock(admin=True, staff=False)

    assert auth.effective_principals("jiji", request) == [
        "consumer:test_id", "group:admin"]


@patch("h.auth.models.User.get_by_userid")
def test_effective_principals_with_staff_user(get_by_userid):
    """If the user is staff it should return a "group:staff" principal."""
    request = MagicMock(client=None)
    get_by_userid.return_value = MagicMock(admin=False, staff=True)

    assert auth.effective_principals("jiji", request) == ["group:staff"]


@patch("h.auth.models.User.get_by_userid")
def test_effective_principals_client_id_and_admin_and_staff(get_by_userid):
    request = MagicMock(client=MagicMock(client_id="test_id"))
    get_by_userid.return_value = MagicMock(admin=True, staff=True)

    assert auth.effective_principals("jiji", request) == [
        "consumer:test_id", "group:admin", "group:staff"]
