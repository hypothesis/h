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
