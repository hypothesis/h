# -*- coding: utf-8 -*-

import datetime
from unittest import mock

import jwt
import pytest

from h.auth import tokens


class TestToken:
    def test_token_with_no_expiry_is_valid(self):
        token = tokens.Token(mock.Mock(expires=None, userid="acct:foo@example.com"))

        assert token.is_valid()

    def test_token_with_future_expiry_is_valid(self):
        token = tokens.Token(
            mock.Mock(userid="acct:foo@example.com", expires=_seconds_from_now(1800))
        )

        assert token.is_valid()

    def test_token_with_past_expiry_is_not_valid(self):
        token = tokens.Token(
            mock.Mock(userid="acct:foo@example.com", expires=_seconds_from_now(-1800))
        )

        assert not token.is_valid()


VALID_TOKEN_EXAMPLES = [
    # Valid
    lambda k: jwt.encode({"exp": _seconds_from_now(3600)}, key=k),
    # Expired, but within leeway
    lambda k: jwt.encode({"exp": _seconds_from_now(-120)}, key=k),
]

INVALID_TOKEN_EXAMPLES = [
    # Expired 1 hour ago
    lambda k: jwt.encode({"exp": _seconds_from_now(-3600)}, key=k),
    # Incorrect encoding key
    lambda k: jwt.encode({"exp": _seconds_from_now(3600)}, key="somethingelse"),
]


class TestAuthToken:
    def test_retrieves_token_for_request(self, pyramid_request):
        pyramid_request.headers["Authorization"] = "Bearer abcdef123"

        result = tokens.auth_token(pyramid_request)

        assert result == "abcdef123"

    def test_returns_none_when_no_authz_header(self, pyramid_request):
        result = tokens.auth_token(pyramid_request)

        assert result is None

    def test_returns_none_for_empty_token(self, pyramid_request):
        pyramid_request.headers["Authorization"] = "Bearer "

        result = tokens.auth_token(pyramid_request)

        assert result is None

    @pytest.mark.parametrize(
        "header",
        [
            "",
            "abcdef123",
            "\x10",
            ".\x00\"Ħ(\x12'𨳂\x05\U000df02a\U00095c2c셀",
            "\U000f022b\t\x07\x1c0\x04\x06",
        ],
    )
    def test_returns_none_for_malformed_header(self, header, pyramid_request):
        pyramid_request.headers["Authorization"] = header

        result = tokens.auth_token(pyramid_request)

        assert result is None


def _seconds_from_now(seconds):
    return datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
