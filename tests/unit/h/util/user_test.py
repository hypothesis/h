import pytest

from h.exceptions import InvalidUserId
from h.util import user as user_util


def test_split_user():
    parts = user_util.split_user("acct:seanh@hypothes.is")
    assert parts == {"username": "seanh", "domain": "hypothes.is"}


def test_split_user_no_match():
    with pytest.raises(InvalidUserId):
        user_util.split_user("donkeys")


class TestGetUserURL:
    def test_it(self, pyramid_request, user):
        assert (
            user_util.get_user_url(user, pyramid_request)
            == f"http://example.com/users/{user.username}"
        )

    def test_it_returns_none_if_authority_does_not_match(self, pyramid_request, user):
        pyramid_request.default_authority = "foo.org"
        assert user_util.get_user_url(user, pyramid_request) is None

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
