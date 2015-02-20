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
        self.client_patcher = patch('h.auth.get_client')
        self.client = self.client_patcher.start()
        self.load_patcher = patch('jwt.api.load')
        self.load = self.load_patcher.start()
        self.verify_patcher = patch('jwt.api.verify_signature')
        self.verify = self.verify_patcher.start()
        self.request = testing.DummyRequest(client=None, user=None)
        self.validator = auth.RequestValidator()
        self.request.registry.settings['h.client_id'] = KEY
        self.request.registry.settings['h.client_secret'] = SECRET

    def tearDown(self):
        self.client_patcher.stop()
        self.load_patcher.stop()
        self.verify_patcher.stop()

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
        self.request.client_id = None
        self.request.client_secret = None
        self.client.return_value = client
        with patch('pyramid.session.check_csrf_token') as csrf:
            csrf.return_value = True
            self.request.session = {'userid': 'hopper'}
            res = self.validator.authenticate_client(self.request)
        assert res is True
        assert self.request.client is client
        assert self.request.user == 'hopper'

    def test_authenticate_client_csrf_not_ok(self):
        self.request.client_id = None
        self.request.client_secret = None
        res = self.validator.authenticate_client(self.request)
        assert res is False
        assert self.request.client is None
        assert self.request.user is None

    def test_validate_bearer_token_client_invalid(self):
        self.client.return_value = None
        self.load.return_value = (
            {'iss': 'fake-client'},
            'input', 'header', 'signature',
        )
        res = self.validator.validate_bearer_token('', None, self.request)
        assert res is False
        self.client.assert_called_once_with(self.request, 'fake-client')

    def test_validate_bearer_token_format_invalid(self):
        self.load.side_effect = jwt.InvalidTokenError
        res = self.validator.validate_bearer_token('', None, self.request)
        assert res is False

    def test_validate_bearer_token_signature_invalid(self):
        client = MockClient(self.request, KEY)
        self.client.return_value = client
        self.load.return_value = (
            {'iss': KEY},
            'input', 'header', 'signature',
        )
        self.verify.side_effect = jwt.InvalidTokenError
        res = self.validator.validate_bearer_token('', [], self.request)
        self.verify.assert_called_with(*self.load.return_value,
                                       key=SECRET,
                                       audience=self.request.host_url,
                                       leeway=ANY)
        assert res is False

    def test_validate_bearer_token_valid(self):
        client = MockClient(self.request, KEY)
        self.client.return_value = client
        self.load.return_value = (
            {'iss': KEY, 'sub': 'citizen'},
            'input', 'header', 'signature',
        )
        res = self.validator.validate_bearer_token('', None, self.request)
        assert res is True
        assert self.request.client is client
        assert self.request.user == 'citizen'
        assert self.request.scopes is None


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
