# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from mock import PropertyMock
import pytest

from h.panels.navbar import navbar
from h.services.group_list import GroupListService


@pytest.mark.usefixtures("routes", "group_list_svc")
class TestNavbar(object):
    def test_it_sets_null_username_when_logged_out(self, req):
        result = navbar({}, req)
        assert result["username"] is None

    def test_it_sets_username_when_logged_in(self, req, user):
        req.user = user
        result = navbar({}, req)

        assert result["username"] == "vannevar"

    def test_it_lists_groups_when_logged_in(self, req, user):
        req.user = user
        result = navbar({}, req)

        assert result["groups_menu_items"] == [
            {
                "title": g.name,
                "link": "http://example.com/groups/" + g.pubid + "/" + g.slug,
            }
            for g in user.groups
        ]

    def test_includes_groups_suggestions_when_logged_in(self, req, user, open_group):
        req.user = user
        result = navbar({}, req)
        assert result["groups_suggestions"] == [
            {
                "name": g.name,
                "pubid": g.pubid,
                "relationship": "Creator" if g.creator == user else None,
            }
            for g in user.groups
        ]

    def test_username_url_when_logged_in(self, req, user):
        req.user = user
        result = navbar({}, req)

        assert result["username_url"] == "http://example.com/users/vannevar"

    def test_it_includes_search_query(self, req):
        req.params["q"] = "tag:question"
        result = navbar({}, req)

        assert result["q"] == "tag:question"

    def test_it_includes_search_url_when_on_user_search(self, req):
        type(req.matched_route).name = PropertyMock(return_value="activity.user_search")
        req.matchdict = {"username": "luke"}

        result = navbar({}, req)
        assert result["search_url"] == "http://example.com/users/luke"

    def test_it_includes_search_url_when_on_group_search(self, req):
        type(req.matched_route).name = PropertyMock(return_value="group_read")
        req.matchdict = {"pubid": "foobar", "slug": "slugbar"}

        result = navbar({}, req)
        assert result["search_url"] == "http://example.com/groups/foobar/slugbar"

    def test_it_includes_default_search_url(self, req):
        result = navbar({}, req)
        assert result["search_url"] == "http://example.com/search"

    def test_it_includes_default_search_url_if_no_matched_route(self, req):
        req.matched_route = None
        result = navbar({}, req)
        assert result["search_url"] == "http://example.com/search"

    @pytest.fixture
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

    @pytest.fixture
    def open_group(self, factories):
        return factories.OpenGroup()

    @pytest.fixture
    def user(self, factories):
        user = factories.User(username="vannevar")
        user.groups = [factories.Group(creator=user), factories.Group()]
        return user

    @pytest.fixture
    def req(self, pyramid_request):
        return pyramid_request

    @pytest.fixture
    def group_list_svc(self, pyramid_config, user):
        svc = mock.create_autospec(GroupListService, spec_set=True, instance=True)
        svc.associated_groups.return_value = user.groups
        pyramid_config.register_service(svc, name="group_list")
        return svc
