from unittest import mock

import pytest
from h_matchers import Any

from h.jinja_extensions.navbar_data import navbar_data


class TestNavbarData:
    def test_it(self, pyramid_request, user):
        pyramid_request.matched_route = None
        pyramid_request.params["q"] = "tag:question"
        pyramid_request.user = user

        result = navbar_data(pyramid_request)

        assert result == {
            "create_group_item": {
                "link": "http://example.com/groups/new",
                "title": "Create new group",
            },
            "groups_menu_items": [
                {
                    "title": group.name,
                    "link": f"http://example.com/groups/{group.pubid}/{group.slug}",
                }
                for group in user.groups
            ],
            "groups_suggestions": [
                {
                    "name": group.name,
                    "pubid": group.pubid,
                    "relationship": "Creator" if group.creator == user else None,
                }
                for group in user.groups
            ],
            "q": "tag:question",
            "search_url": Any.string(),
            "settings_menu_items": [
                {"link": "http://example.com/account", "title": "Account details"},
                {"link": "http://example.com/account/profile", "title": "Edit profile"},
                {
                    "link": "http://example.com/account/notifications",
                    "title": "Notifications",
                },
                {"link": "http://example.com/account/developer", "title": "Developer"},
            ],
            "signout_item": {"link": "http://example.com/logout", "title": "Sign out"},
            "username": user.username,
            "username_url": f"http://example.com/users/{user.username}",
        }

    def test_it_with_no_user(self, pyramid_request, group_list_service):
        pyramid_request.user = None
        group_list_service.associated_groups.return_value = []

        result = navbar_data(pyramid_request)

        assert result == Any.dict.containing(
            {
                "groups_menu_items": [],
                "groups_suggestions": [],
                "username": None,
                "username_url": None,
            }
        )

    @pytest.mark.parametrize(
        "matched_route, matchdict, search_url",
        (
            (None, {}, "http://example.com/search"),
            (
                "activity.user_search",
                {"username": "luke"},
                "http://example.com/users/luke",
            ),
            (
                "group_read",
                {"pubid": "foobar", "slug": "slugbar"},
                "http://example.com/groups/foobar/slugbar",
            ),
        ),
    )
    def test_search_url(self, pyramid_request, matched_route, matchdict, search_url):
        type(pyramid_request.matched_route).name = mock.PropertyMock(
            return_value=matched_route
        )
        pyramid_request.matchdict = matchdict

        result = navbar_data(pyramid_request)

        assert result["search_url"] == search_url

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
