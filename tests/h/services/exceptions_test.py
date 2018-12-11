# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.services import exceptions


class TestServiceError(object):
    def test_it_is_an_exception(self):
        exc = exceptions.ServiceError("a message")

        assert isinstance(exc, Exception)
        assert isinstance(exc, exceptions.ServiceError)

    def test_it_can_set_message(self):
        exc = exceptions.ServiceError("a message")

        assert "a message" in repr(exc)


class TestValidationError(object):
    def test_it_extends_ServiceError(self):
        exc = exceptions.ValidationError("some message")

        assert isinstance(exc, exceptions.ValidationError)
        assert isinstance(exc, exceptions.ServiceError)

    def test_it_can_set_message(self):
        exc = exceptions.ValidationError("a message")

        assert "a message" in repr(exc)


class TestConflictError(object):
    def test_it_extends_ServiceError(self):
        exc = exceptions.ConflictError("some message")

        assert isinstance(exc, exceptions.ConflictError)
        assert isinstance(exc, exceptions.ServiceError)

    def test_it_can_set_message(self):
        exc = exceptions.ConflictError("a message")

        assert "a message" in repr(exc)
