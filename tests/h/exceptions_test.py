# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h import exceptions


class TestAPIError(object):
    def test_message(self):
        exc = exceptions.APIError('some message')

        assert str(exc) == 'some message'

    def test_default_status_code(self):
        exc = exceptions.APIError('some message')

        assert exc.status_code == 500

    def test_custom_status_code(self):
        exc = exceptions.APIError('some message', status_code=418)

        assert exc.status_code == 418


class TestClientUnauthorized(object):
    def test_message(self):
        exc = exceptions.ClientUnauthorized()

        assert 'credentials are invalid' in str(exc)

    def test_status_code(self):
        exc = exceptions.ClientUnauthorized()

        assert exc.status_code == 403


class TestConflictError(object):
    def test_it_returns_the_correct_http_status(self):
        exc = exceptions.ConflictError()

        assert exc.status_code == 409

    def test_it_sets_default_message_if_none_provided(self):
        exc = exceptions.ConflictError()

        assert str(exc) == "Conflict"

    def test_it_sets_provided_message(self):
        exc = exceptions.ConflictError("nah, that's no good")

        assert str(exc) == "nah, that's no good"


class TestOAuthTokenError(object):
    def test_it_sets_type_and_message(self):
        exc = exceptions.OAuthTokenError('boom', 'mytype')

        assert exc.type == 'mytype'
        assert str(exc) == 'boom'

    def test_it_sets_default_response_code(self):
        exc = exceptions.OAuthTokenError('boom', 'mytype')

        assert exc.status_code == 400

    def test_it_sets_custom_response_code(self):
        exc = exceptions.OAuthTokenError('boom', 'mytype', 500)

        assert exc.status_code == 500


class TestPayloadError(object):
    def test_it_sets_default_message_and_status(self):
        exc = exceptions.PayloadError()

        assert exc.status_code == 400
        assert str(exc) == 'Expected a valid JSON payload, but none was found!'
