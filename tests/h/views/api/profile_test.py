# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPBadRequest

from h.services.group_list import GroupListService
from h.views.api import profile as views


class TestProfile(object):
    def test_profile_view_proxies_to_session(self, session_profile, pyramid_request):
        result = views.profile(pyramid_request)

        session_profile.assert_called_once_with(pyramid_request, None)
        assert result == session_profile.return_value

    def test_profile_passes_authority_parameter(self, session_profile, pyramid_request):
        pyramid_request.params = {"authority": "foo.com"}

        result = views.profile(pyramid_request)

        session_profile.assert_called_once_with(pyramid_request, "foo.com")
        assert result == session_profile.return_value


@pytest.mark.usefixtures("user_service", "session_profile")
class TestUpdatePreferences(object):
    def test_updates_preferences(self, pyramid_request, user, user_service):
        pyramid_request.json_body = {"preferences": {"show_sidebar_tutorial": True}}

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
            user, show_sidebar_tutorial=True
        )

    def test_handles_invalid_preferences_error(self, pyramid_request, user_service):
        user_service.update_preferences.side_effect = TypeError("uh oh, wrong prefs")

        with pytest.raises(HTTPBadRequest) as exc:
            views.update_preferences(pyramid_request)

        assert str(exc.value) == "uh oh, wrong prefs"

    def test_handles_missing_preferences_payload(self, pyramid_request):
        pyramid_request.json_body = {"foo": "bar"}

        # should not raise
        views.update_preferences(pyramid_request)

    def test_returns_session_profile(self, pyramid_request, session_profile):
        result = views.update_preferences(pyramid_request)

        assert result == session_profile.return_value

    @pytest.fixture
    def user_service(self, pyramid_config):
        svc = mock.Mock()
        pyramid_config.register_service(svc, name="user")
        return svc


@pytest.mark.usefixtures("group_list_service", "GroupContext", "GroupsJSONPresenter")
class TestProfileGroups(object):
    def test_it_proxies_to_group_list_service(
        self, pyramid_request, group_list_service
    ):
        views.profile_groups(pyramid_request)

        group_list_service.user_groups.assert_called_once_with(
            user=pyramid_request.user
        )

    def test_it_converts_group_models_to_contexts(
        self, pyramid_request, group_list_service, GroupContext
    ):
        group_list_service.user_groups.return_value = [1, 2, 3]
        views.profile_groups(pyramid_request)

        GroupContext.assert_has_calls(
            [
                mock.call(1, pyramid_request),
                mock.call(2, pyramid_request),
                mock.call(3, pyramid_request),
            ]
        )

    def test_it_returns_presented_groups(
        self, pyramid_request, group_list_service, GroupsJSONPresenter
    ):
        group_list_service.user_groups.return_value = [1, 2, 3]

        result = views.profile_groups(pyramid_request)

        assert result == GroupsJSONPresenter([1, 2, 3]).asdicts.return_value

    def test_it_proxies_expand_to_presenter(
        self, pyramid_request, group_list_service, GroupsJSONPresenter
    ):
        pyramid_request.params["expand"] = "organization"
        group_list_service.user_groups.return_value = [1, 2, 3]

        views.profile_groups(pyramid_request)

        GroupsJSONPresenter([1, 2, 3]).asdicts.assert_called_once_with(
            expand=["organization"]
        )


@pytest.fixture
def user(factories):
    return factories.User.build()


@pytest.fixture
def pyramid_request(pyramid_request, user):
    pyramid_request.user = user
    pyramid_request.json_body = {}
    return pyramid_request


@pytest.fixture
def group_list_service(pyramid_config):
    svc = mock.create_autospec(GroupListService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_list")
    return svc


@pytest.fixture
def GroupContext(patch):
    return patch("h.views.api.profile.GroupContext")


@pytest.fixture
def GroupsJSONPresenter(patch):
    return patch("h.views.api.profile.GroupsJSONPresenter")


@pytest.fixture
def session_profile(patch):
    return patch("h.session.profile")
