from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPBadRequest

from h.schemas import ValidationError
from h.services.group_list import GroupListService
from h.views.api import profile as views


class TestProfile:
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
class TestUpdatePreferences:
    def test_updates_preferences(self, pyramid_request, user, user_service):
        pyramid_request.json_body = {"preferences": {"show_sidebar_tutorial": True}}

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
            user, show_sidebar_tutorial=True
        )

    def test_updates_preferences_youtube_gdpr_banner(
        self, pyramid_request, user, user_service
    ):
        pyramid_request.json_body = {"preferences": {"show_youtube_gdpr_banner": False}}

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
            user, show_youtube_gdpr_banner=False
        )

    def test_updates_instructor_survey_response(
        self, pyramid_request, user, user_service
    ):
        user.email = "someone@stanford.edu"
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "instructor"}
        }

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
            user, instructor_survey_response="instructor"
        )

    def test_rejects_instructor_survey_response_from_third_party(
        self, pyramid_request, user, user_service
    ):
        user.email = "someone@stanford.edu"
        user.authority = "thirdparty.example.org"
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "instructor"}
        }

        with pytest.raises(ValidationError) as exc:
            views.update_preferences(pyramid_request)

        assert "not available to this user" in str(exc.value)
        user_service.update_preferences.assert_not_called()

    def test_rejects_instructor_survey_response_from_non_edu_email(
        self, pyramid_request, user, user_service
    ):
        user.email = "someone@gmail.com"
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "instructor"}
        }

        with pytest.raises(ValidationError):
            views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_not_called()

    def test_rejects_instructor_survey_response_when_flag_is_off(
        self, pyramid_request, user, user_service
    ):
        # The flag is the kill switch: turning it off stops answers being
        # recorded, not just the panel being offered. Not absolute, though --
        # the ?__feature__[instructor_survey] override outranks it here as
        # everywhere else.
        user.email = "someone@stanford.edu"
        pyramid_request.feature.flags["instructor_survey"] = False
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "instructor"}
        }

        with pytest.raises(ValidationError):
            views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_not_called()

    def test_ignores_instructor_survey_response_when_already_answered(
        self, pyramid_request, user, user_service
    ):
        # A retry after a lost response, or a dismissal in a second sidebar
        # whose profile predates the first answer, must not overwrite the
        # answer -- and must not be an error the user sees either.
        user.email = "someone@stanford.edu"
        user.edu_role_survey_response = "instructor"
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "dismissed"}
        }

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(user)

    def test_keeps_other_preferences_when_survey_is_already_answered(
        self, pyramid_request, user, user_service
    ):
        user.email = "someone@stanford.edu"
        user.edu_role_survey_response = "instructor"
        pyramid_request.json_body = {
            "preferences": {
                "instructor_survey_response": "dismissed",
                "show_sidebar_tutorial": True,
            }
        }

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
            user, show_sidebar_tutorial=True
        )

    def test_rejects_instructor_survey_response_when_flag_is_off_and_already_answered(
        self, pyramid_request, user, user_service
    ):
        # Having answered before doesn't earn a pass through the kill switch:
        # the answer is rejected, not quietly dropped as a stale duplicate
        # would be. Same for anyone else the survey isn't for any more.
        user.email = "someone@stanford.edu"
        user.edu_role_survey_response = "dismissed"
        pyramid_request.feature.flags["instructor_survey"] = False
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "instructor"}
        }

        with pytest.raises(ValidationError):
            views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_not_called()

    def test_rejects_instructor_survey_response_from_third_party_already_answered(
        self, pyramid_request, user, user_service
    ):
        user.email = "someone@stanford.edu"
        user.authority = "thirdparty.example.org"
        user.edu_role_survey_response = "dismissed"
        pyramid_request.json_body = {
            "preferences": {"instructor_survey_response": "instructor"}
        }

        with pytest.raises(ValidationError):
            views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_not_called()

    def test_allows_other_preferences_from_third_party(
        self, pyramid_request, user, user_service
    ):
        user.authority = "thirdparty.example.org"
        pyramid_request.json_body = {"preferences": {"show_sidebar_tutorial": True}}

        views.update_preferences(pyramid_request)

        user_service.update_preferences.assert_called_once_with(
            user, show_sidebar_tutorial=True
        )

    @pytest.mark.parametrize("preferences", [None, 5, "instructor_survey_response"])
    def test_handles_non_mapping_preferences(self, pyramid_request, user, preferences):
        # A non-mapping body has to keep producing the generic 400 it always
        # did, and must not be mistaken for a survey answer -- note the third
        # case, where `"instructor_survey_response" in preferences` would be
        # true as a substring test. The user is ineligible here, so routing it
        # to the survey guard by mistake would raise ValidationError instead.
        user.email = "someone@gmail.com"
        pyramid_request.json_body = {"preferences": preferences}

        with pytest.raises(HTTPBadRequest) as exc:
            views.update_preferences(pyramid_request)

        assert not isinstance(exc.value, ValidationError)

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


@pytest.mark.usefixtures("group_list_service", "GroupsJSONPresenter")
class TestProfileGroups:
    @pytest.mark.parametrize(
        "expand",
        ([], ["organization"], ["organization", "scopes"]),
    )
    def test_it(self, pyramid_request, expand, group_list_service, GroupsJSONPresenter):
        for param in expand:
            pyramid_request.GET.add("expand", param)

        result = views.profile_groups(pyramid_request)

        group_list_service.user_groups.assert_called_once_with(
            user=pyramid_request.user
        )
        GroupsJSONPresenter.assert_called_once_with(
            group_list_service.user_groups.return_value, pyramid_request
        )
        GroupsJSONPresenter.return_value.asdicts.assert_called_once_with(expand=expand)
        assert result == GroupsJSONPresenter.return_value.asdicts.return_value


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
def GroupsJSONPresenter(patch):
    return patch("h.views.api.profile.GroupsJSONPresenter")


@pytest.fixture
def session_profile(patch):
    return patch("h.session.profile")
