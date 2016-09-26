# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.exceptions import APIError


class TestAPIError(object):
    def test_message(self):
        exc = APIError('some message')

        assert exc.message == 'some message'

    def test_default_status_code(self):
        exc = APIError('some message')

        assert exc.status_code == 500

    def test_custom_status_code(self):
        exc = APIError('some message', status_code=418)

        assert exc.status_code == 418
