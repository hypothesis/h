# -*- coding: utf-8 -*-
from collections import namedtuple
import unittest

from mock import MagicMock
from pyramid.testing import DummyRequest

from h.oauth.tokens import AnnotatorToken

FakeClient = namedtuple('FakeClient', ['client_id', 'client_secret'])


class TestAnnotatorToken(unittest.TestCase):

    def setUp(self):
        self.validator = MagicMock()
        self.tok = AnnotatorToken(request_validator=self.validator)

        self.client = FakeClient('someclient', 'secretz!')
        self.request = DummyRequest(
            access_token=None,
            client=self.client,
            state=None,
            extra_credentials=None,
            user=None,
            scopes=['world'],
        )
        self.request.headers['X-Annotator-Auth-Token'] = 'civilian'

    def test_created_token_has_access_token(self):
        res = self.tok.create_token(self.request)
        assert res['access_token'] is not None

    def test_validate_request(self):
        self.tok.validate_request(self.request)
        self.validator.validate_bearer_token.assert_called_with(
            'civilian',
            ['world'],
            self.request,
        )

    def test_estimate_type(self):
        assert self.tok.estimate_type(self.request) == 0
        del self.request.headers['X-Annotator-Auth-Token']
        assert self.tok.estimate_type(self.request) == 9
