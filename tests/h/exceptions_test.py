# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.exceptions import APIError, ClientUnauthorized, ConflictError


class TestAPIError(object):
    def test_message(self):
        exc = APIError('some message')

        assert str(exc) == 'some message'

    def test_default_status_code(self):
        exc = APIError('some message')

        assert exc.status_code == 500

    def test_custom_status_code(self):
        exc = APIError('some message', status_code=418)

        assert exc.status_code == 418


class TestClientUnauthorized(object):
    def test_message(self):
        exc = ClientUnauthorized()

        assert 'credentials are invalid' in str(exc)

    def test_status_code(self):
        exc = ClientUnauthorized()

        assert exc.status_code == 403


class TestConflictError(object):
    def test_it_returns_the_correct_http_status(self):
        exc = ConflictError()

        assert exc.status_code == 409

    def test_it_sets_default_message_if_none_provided(self):
        exc = ConflictError()

        assert exc.message == "Conflict"

    def test_it_sets_provided_message(self):
        exc = ConflictError("nah, that's no good")

        assert exc.message == "nah, that's no good"
