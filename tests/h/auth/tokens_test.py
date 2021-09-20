import datetime

import pytest
from pytest import param

from h.auth import tokens


def _seconds_from_now(seconds):
    return datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)


class TestToken:
    @pytest.mark.parametrize(
        "expires,is_valid",
        (
            param(None, True, id="no expiry"),
            param(_seconds_from_now(1800), True, id="future expiry"),
            param(_seconds_from_now(-1800), False, id="past expiry"),
        ),
    )
    def test_it(self, expires, is_valid, factories):
        token = tokens.Token(
            factories.OAuth2Token(userid="acct:foo@example.com", expires=expires)
        )

        assert token.is_valid() == is_valid


class TestAuthToken:
    @pytest.mark.parametrize(
        "header,expected",
        (
            ("Bearer abcdef123", "abcdef123"),
            (None, None),
            ("Bearer ", None),
            ("", None),
            ("abcdef123", None),
            ("\x10", None),
            (".\x00\"Ħ(\x12'𨳂\x05\U000df02a\U00095c2c셀", None),
            ("\U000f022b\t\x07\x1c0\x04\x06", None),
        ),
    )
    def test_it(self, pyramid_request, header, expected):
        if header is not None:
            pyramid_request.headers["Authorization"] = header

        assert tokens.auth_token(pyramid_request) == expected
