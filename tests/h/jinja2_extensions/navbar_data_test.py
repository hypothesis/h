from unittest import mock

import pytest

from h.jinja_extensions.navbar_data import navbar_data


class TestNavbarData:
    def test_it_sets_null_username_when_logged_out(self, pyramid_request):
        result = navbar_data(pyramid_request)

        assert result["username"] is None

    def test_it_sets_username_when_logged_in(self, pyramid_request, user):
        pyramid_request.user = user

        result = navbar_data(pyramid_request)

        assert result["username"] == user.username

    def test_it_lists_groups_when_logged_in(self, pyramid_request, user):
        pyramid_request.user = user

        result = navbar_data(pyramid_request)

        assert result["groups_menu_items"] == [
            {
                "title": g.name,
                "link": "http://example.com/groups/" + g.pubid + "/" + g.slug,
            }
            for g in user.groups
        ]

    def test_includes_groups_suggestions_when_logged_in(self, pyramid_request, user):
        pyramid_request.user = user

        result = navbar_data(pyramid_request)

        assert result["groups_suggestions"] == [
            {
                "name": group.name,
                "pubid": group.pubid,
                "relationship": "Creator" if group.creator == user else None,
            }
            for group in user.groups
        ]

    def test_username_url_when_logged_in(self, pyramid_request, user):
        pyramid_request.user = user

        result = navbar_data(pyramid_request)

        assert result["username_url"] == f"http://example.com/users/{user.username}"

    def test_it_includes_search_query(self, pyramid_request):
        pyramid_request.params["q"] = "tag:question"

        result = navbar_data(pyramid_request)

        assert result["q"] == "tag:question"

    def test_it_includes_search_url_when_on_user_search(self, pyramid_request):
        type(pyramid_request.matched_route).name = mock.PropertyMock(
            return_value="activity.user_search"
        )
        pyramid_request.matchdict = {"username": "luke"}

        result = navbar_data(pyramid_request)

        assert result["search_url"] == "http://example.com/users/luke"

    def test_it_includes_search_url_when_on_group_search(self, pyramid_request):
        type(pyramid_request.matched_route).name = mock.PropertyMock(
            return_value="group_read"
        )
        pyramid_request.matchdict = {"pubid": "foobar", "slug": "slugbar"}

        result = navbar_data(pyramid_request)

        assert result["search_url"] == "http://example.com/groups/foobar/slugbar"

    def test_it_includes_default_search_url(self, pyramid_request):
        result = navbar_data(pyramid_request)

        assert result["search_url"] == "http://example.com/search"

    def test_it_includes_default_search_url_if_no_matched_route(self, pyramid_request):
        pyramid_request.matched_route = None

        result = navbar_data(pyramid_request)

        assert result["search_url"] == "http://example.com/search"

    @pytest.fixture
    def open_group(self, factories):
        return factories.OpenGroup()

    @pytest.fixture
    def user(self, factories):
        user = factories.User()
        user.groups = [factories.Group(creator=user), factories.Group()]
        return user

    @pytest.fixture(autouse=True)
    def group_list_service(self, group_list_service, user):
        group_list_service.associated_groups.return_value = user.groups
        return group_list_service

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("account", "/account")
        pyramid_config.add_route("account_profile", "/account/profile")
        pyramid_config.add_route("account_notifications", "/account/notifications")
        pyramid_config.add_route("account_developer", "/account/developer")
        pyramid_config.add_route("activity.search", "/search")
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("group_create", "/groups/new")
        pyramid_config.add_route("group_read", "/groups/:pubid/:slug")
        pyramid_config.add_route("logout", "/logout")
