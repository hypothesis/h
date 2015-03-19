# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
import mock
import unittest

from oauthlib.common import Request
from oauthlib.oauth2.rfc6749 import errors
from oauthlib.oauth2.rfc6749.tokens import BearerToken

from h.oauth import JWTBearerGrant, JWT_BEARER


class JWTBearerGrantTest(unittest.TestCase):

    def setUp(self):
        mock_client = mock.MagicMock()
        mock_client.user.return_value = 'mocked user'
        self.request = Request('http://a.b/path')
        self.request.assertion = 'mocked assertion'
        self.request.grant_type = JWT_BEARER
        self.request.client = mock_client
        self.request.scope = 'foo'
        self.mock_validator = mock.MagicMock()
        self.auth = JWTBearerGrant(request_validator=self.mock_validator)

    def test_create_token_response(self):
        bearer = BearerToken(self.mock_validator)
        headers, body, status_code = self.auth.create_token_response(
            self.request, bearer)
        token = json.loads(body)
        self.assertIn('access_token', token)
        self.assertIn('token_type', token)
        self.assertIn('expires_in', token)
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertTrue(self.mock_validator.client_authentication_required.called)
        self.assertTrue(self.mock_validator.validate_bearer_token.called)

    def test_create_token_inherit_scope(self):
        self.request.scope = None
        self.mock_validator.get_original_scopes.return_value = ['foo', 'bar']
        bearer = BearerToken(self.mock_validator)
        headers, body, status_code = self.auth.create_token_response(
            self.request, bearer)
        token = json.loads(body)
        self.assertIn('access_token', token)
        self.assertIn('token_type', token)
        self.assertIn('expires_in', token)
        self.assertEqual(token['scope'], 'foo bar')

    def test_create_token_within_original_scope(self):
        self.mock_validator.get_original_scopes.return_value = ['baz']
        self.mock_validator.is_within_original_scope.return_value = True
        bearer = BearerToken(self.mock_validator)
        headers, body, status_code = self.auth.create_token_response(
            self.request, bearer)
        token = json.loads(body)
        self.assertIn('access_token', token)
        self.assertIn('token_type', token)
        self.assertIn('expires_in', token)
        self.assertEqual(token['scope'], 'foo')

    def test_invalid_scope(self):
        self.mock_validator.get_original_scopes.return_value = ['baz']
        self.mock_validator.is_within_original_scope.return_value = False
        bearer = BearerToken(self.mock_validator)
        headers, body, status_code = self.auth.create_token_response(
            self.request, bearer)
        token = json.loads(body)
        self.assertEqual(token['error'], 'invalid_scope')
        self.assertEqual(status_code, 401)

    def test_invalid_token(self):
        self.mock_validator.validate_bearer_token.return_value = False
        bearer = BearerToken(self.mock_validator)
        headers, body, status_code = self.auth.create_token_response(
            self.request, bearer)
        token = json.loads(body)
        self.assertEqual(token['error'], 'invalid_grant')
        self.assertEqual(status_code, 401)

    def test_invalid_client(self):
        self.mock_validator.authenticate_client.return_value = False
        bearer = BearerToken(self.mock_validator)
        headers, body, status_code = self.auth.create_token_response(
            self.request, bearer)
        token = json.loads(body)
        self.assertEqual(token['error'], 'invalid_client')
        self.assertEqual(status_code, 401)

    def test_authentication_required(self):
        """
        ensure client_authentication_required() is properly called
        """
        self.mock_validator.authenticate_client.return_value = False
        self.mock_validator.authenticate_client_id.return_value = False
        self.request.code = 'waffles'
        self.assertRaises(errors.InvalidClientError, self.auth.validate_token_request,
                          self.request)
        self.mock_validator.client_authentication_required.assert_called_once_with(self.request)

    def test_invalid_grant_type(self):
        self.request.grant_type = 'wrong type'
        self.assertRaises(errors.UnsupportedGrantTypeError,
                          self.auth.validate_token_request, self.request)

    def test_invalid_assertion(self):
        # invalid assertion
        self.mock_validator.validate_bearer_token.return_value = False
        self.assertRaises(errors.InvalidGrantError,
                          self.auth.validate_token_request, self.request)
        # no token provided
        del self.request.assertion
        self.assertRaises(errors.InvalidRequestError,
                          self.auth.validate_token_request, self.request)

    def test_invalid_scope_original_scopes_empty(self):
        self.mock_validator.validate_bearer_token.return_value = True
        self.mock_validator.is_within_original_scope.return_value = False
        self.assertRaises(errors.InvalidScopeError,
                          self.auth.validate_token_request, self.request)

    def test_valid_token_request(self):
        self.request.scope = 'foo bar'
        self.mock_validator.get_original_scopes = mock.Mock()
        self.mock_validator.get_original_scopes.return_value = 'foo bar baz'
        self.auth.validate_token_request(self.request)
        self.assertEqual(self.request.scopes, self.request.scope.split())
        # all ok but without request.scope
        del self.request.scope
        self.auth.validate_token_request(self.request)
        self.assertEqual(self.request.scopes, 'foo bar baz'.split())
