# -*- coding: utf-8 -*-
from collections import namedtuple
import unittest

from annotator.auth import TokenInvalid
from mock import patch
from pyramid.testing import DummyRequest

from h.authorization import RequestValidator
from h.security import WEB_SCOPES

FakeClient = namedtuple('FakeClient', ['client_id', 'client_secret'])


class TestRequestValidator(unittest.TestCase):

    def setUp(self):
        self.client = FakeClient('someclient', 'somesecret')
        self.request = DummyRequest(
            access_token=None,
            client=None,
            client_id=None,
            client_secret=None,
            state=None,
            extra_credentials=None,
            user=None,
            scopes=['world'],
            get_client=lambda _cid: self.client,
        )
        self.request.registry.web_client = self.client
        self.validator = RequestValidator()

        self.decode_patcher = patch('annotator.auth.decode_token')
        self.decode = self.decode_patcher.start()

    def test_authenticate_client_ok(self):
        self.request.client_id = 'someclient'
        self.request.client_secret = 'somesecret'
        res = self.validator.authenticate_client(self.request)
        assert res is True

    def test_authenticate_client_not_ok(self):
        res = self.validator.authenticate_client(self.request)
        assert res is False

        self.request.client_id = 'someclient'
        self.request.client_secret = 'sauce'
        res = self.validator.authenticate_client(self.request)
        assert res is False

    def test_authenticate_client_web_ok(self):
        with patch('h.authorization.check_csrf_token') as csrf:
            csrf.return_value = True
            res = self.validator.authenticate_client(self.request)
            assert res is True

    def test_authenticate_client_web_not_ok(self):
        res = self.validator.authenticate_client(self.request)
        assert res is False

    def test_validate_bearer_token_invalid(self):
        self.decode.side_effect = TokenInvalid
        res = self.validator.validate_bearer_token('', [], self.request)
        assert res is False

    def test_validate_bearer_token_valid(self):
        self.decode.return_value = {'userId': 'citizen', 'scopes': ['world']}
        res = self.validator.validate_bearer_token('', [], self.request)
        assert res is True
        assert self.request.client is self.client
        assert self.request.user == 'citizen'
        assert self.request.scopes == ['world']

    def test_validate_scopes_ok(self):
        client = FakeClient('other', 'secret')
        res = self.validator.validate_scopes(
            client.client_id,
            [],
            client,
            self.request
        )
        assert res is True

    def test_validate_scopes_not_ok(self):
        client = FakeClient('other', 'secret')
        res = self.validator.validate_scopes(
            client.client_id,
            ['bogus'],
            client,
            self.request
        )
        assert res is False

    def test_validate_scopes_web_ok(self):
        res = self.validator.validate_scopes(
            self.client.client_id,
            WEB_SCOPES,
            self.client,
            self.request
        )
        assert res is True

    def test_validate_scopes_web_not_ok(self):
        res = self.validator.validate_scopes(
            self.client.client_id,
            WEB_SCOPES + ['bogus'],
            self.client,
            self.request
        )
        assert res is False
