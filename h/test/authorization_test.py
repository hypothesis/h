# -*- coding: utf-8 -*-
from collections import namedtuple
import datetime
import unittest

import jwt
from mock import ANY, patch
from pyramid.testing import DummyRequest

from h.authorization import RequestValidator
from h.security import WEB_SCOPES

EPOCH = datetime.datetime(1970, 1, 1)
FakeClient = namedtuple('FakeClient', ['client_id', 'client_secret'])


def posix_seconds(t):
    return int((t - EPOCH).total_seconds())


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

    def test_validate_bearer_token(self):
        now = datetime.datetime.utcnow().replace(microsecond=0)
        ttl = datetime.timedelta(seconds=30)
        exp = posix_seconds(now + ttl)
        payload = {
            'aud': self.request.host_url,
            'sub': 'citizen',
            'exp': exp,
            'iss': self.client.client_id,
        }
        token = jwt.encode(payload, self.client.client_secret)

        with patch('jwt.verify_signature') as verify:
            res = self.validator.validate_bearer_token(token, [], self.request)

            verify.assert_called_with(payload, ANY, ANY, ANY,
                                      key=self.client.client_secret,
                                      audience=payload['aud'],
                                      issuer=payload['iss'],
                                      leeway=ANY)

            assert res is True
            assert self.request.client is self.client
            assert self.request.scopes == WEB_SCOPES
            assert self.request.user == 'citizen'


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
