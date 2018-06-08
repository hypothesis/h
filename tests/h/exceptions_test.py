# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.exceptions import APIError, ClientUnauthorized


class TestAPIError(object):
    def test_message(self):
        exc = APIError("some message")

        assert str(exc) == "some message"

    def test_default_status_code(self):
        exc = APIError("some message")

        assert exc.status_code == 500

    def test_custom_status_code(self):
        exc = APIError("some message", status_code=418)

        assert exc.status_code == 418


class TestClientUnauthorized(object):
    def test_message(self):
        exc = ClientUnauthorized()

        assert "credentials are invalid" in str(exc)

    def test_status_code(self):
        exc = ClientUnauthorized()

        assert exc.status_code == 403
