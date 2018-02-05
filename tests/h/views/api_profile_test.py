# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.exceptions import APIError
from h.views import api_profile


class TestProfile(object):
    def test_profile_view_proxies_to_session(self, session_profile, pyramid_request):
        result = api_profile.profile(pyramid_request)

        session_profile.assert_called_once_with(pyramid_request, None)
        assert result == session_profile.return_value

    def test_profile_passes_authority_parameter(self, session_profile, pyramid_request):
        pyramid_request.params = {'authority': 'foo.com'}

        result = api_profile.profile(pyramid_request)

        session_profile.assert_called_once_with(pyramid_request, 'foo.com')
        assert result == session_profile.return_value


@pytest.mark.usefixtures('user_service', 'session_profile')
class TestUpdatePreferences(object):
    def test_updates_preferences(self, pyramid_request, user, user_service):
        pyramid_request.json_body = {'preferences': {'show_sidebar_tutorial': True}}

        api_profile.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
                user, show_sidebar_tutorial=True)

    def test_handles_invalid_preferences_error(self, pyramid_request, user_service):
        user_service.update_preferences.side_effect = TypeError('uh oh, wrong prefs')

        with pytest.raises(APIError) as exc:
            api_profile.update_preferences(pyramid_request)

        assert exc.value.message == 'uh oh, wrong prefs'

    def test_handles_missing_preferences_payload(self, pyramid_request):
        pyramid_request.json_body = {'foo': 'bar'}

        # should not raise
        api_profile.update_preferences(pyramid_request)

    def test_returns_session_profile(self, pyramid_request, session_profile):
        result = api_profile.update_preferences(pyramid_request)

        assert result == session_profile.return_value

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def user_service(self, pyramid_config):
        svc = mock.Mock()
        pyramid_config.register_service(svc, name='user')
        return svc


@pytest.fixture
def session_profile(patch):
    return patch('h.session.profile')
