import pytest

from h.exceptions import InvalidUserId
from h.util import user as user_util


def test_split_user():
    parts = user_util.split_user("acct:seanh@hypothes.is")
    assert parts == {"username": "seanh", "domain": "hypothes.is"}


def test_split_user_no_match():
    with pytest.raises(InvalidUserId):
        user_util.split_user("donkeys")
