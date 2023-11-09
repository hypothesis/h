import pytest

from h.jinja_extensions.back_link_label import back_link_label


@pytest.mark.usefixtures("routes")
class TestBackLinkLabel:
    @pytest.mark.parametrize(
        "referrer,label",
        [
            ("https://example.com/users/current_user", "Back to your profile page"),
            (
                "https://example.com/users/current_user?q=tag:foo",
                "Back to your profile page",
            ),
            ("https://example.com/users/other_user", None),
            ("https://example.com/groups/abc/def", "Back to group overview page"),
            ("https://example.com/search", None),
            (None, None),
        ],
    )
    def test_it_sets_back_label(self, pyramid_request, referrer, label):
        pyramid_request.referrer = referrer

        assert back_link_label(pyramid_request) == label

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        pyramid_request.user = factories.User(username="current_user")
        return pyramid_request

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("group_read", "/groups/{pubid}/{slug}")
        return pyramid_config
