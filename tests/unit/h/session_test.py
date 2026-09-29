from unittest import mock

import pytest

from h import session
from h.services.group_list import GroupListService


class TestModel:
    def test_proxies_group_lookup_to_service(self, authenticated_request):
        svc = authenticated_request.find_service(name="group_list")

        session.model(authenticated_request)

        svc.session_groups.assert_called_once_with(
            user=authenticated_request.user,
            authority=authenticated_request.default_authority,
        )

    def test_proxies_group_lookup_to_service_for_unauth(self, unauthenticated_request):
        svc = unauthenticated_request.find_service(name="group_list")

        session.model(unauthenticated_request)

        svc.session_groups.assert_called_once_with(
            authority=unauthenticated_request.default_authority, user=None
        )

    def test_open_group_is_public(self, unauthenticated_request, world_group):
        svc = unauthenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [world_group]

        model = session.model(unauthenticated_request)

        assert model["groups"][0]["public"]

    def test_private_group_is_not_public(self, authenticated_request, factories):
        a_group = factories.Group()
        svc = authenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [a_group]

        model = session.model(authenticated_request)

        assert not model["groups"][0]["public"]

    def test_open_group_has_no_url(self, unauthenticated_request, world_group):
        svc = unauthenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [world_group]

        model = session.model(unauthenticated_request)

        assert not model["groups"][0].get("url")

    def test_private_group_has_url(self, authenticated_request, factories):
        a_group = factories.Group()
        svc = authenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [a_group]

        model = session.model(authenticated_request)

        assert model["groups"][0]["url"]

    def test_includes_features(self, authenticated_request):
        feature_dict = {"feature_one": True, "feature_two": False}
        authenticated_request.set_features(feature_dict)

        assert session.model(authenticated_request)["features"] == feature_dict

    def test_anonymous_hides_sidebar_tutorial(self, unauthenticated_request):
        preferences = session.model(unauthenticated_request)["preferences"]

        assert "show_sidebar_tutorial" not in preferences

    @pytest.mark.parametrize("dismissed", [True, False])
    def test_authenticated_sidebar_tutorial(self, authenticated_request, dismissed):
        authenticated_request.set_sidebar_tutorial_dismissed(dismissed)

        preferences = session.model(authenticated_request)["preferences"]

        if dismissed:
            assert "show_sidebar_tutorial" not in preferences
        else:
            assert preferences["show_sidebar_tutorial"] is True

    def test_anonymous_hides_youtube_gdpr_banner(self, unauthenticated_request):
        preferences = session.model(unauthenticated_request)["preferences"]

        assert "show_youtube_gdpr_banner" not in preferences

    def test_it_never_includes_the_instructor_survey(self, authenticated_request):
        # Not even for a user who is being shown the survey -- `profile()` is
        # what tells them, and there is a test for that. This model is
        # published to *other* users' sidebars (see the comment in
        # session.model), so the survey has no business travelling in it.
        authenticated_request.set_edu_role_survey(None)

        preferences = session.model(authenticated_request)["preferences"]

        assert "show_instructor_survey" not in preferences

    @pytest.mark.parametrize("dismissed", [True, False])
    def test_authenticated_youtube_gdpr_banner(self, authenticated_request, dismissed):
        authenticated_request.set_youtube_gdpr_banner_dismissed(dismissed)

        preferences = session.model(authenticated_request)["preferences"]

        if dismissed:
            assert "show_youtube_gdpr_banner" not in preferences
        else:
            assert preferences["show_youtube_gdpr_banner"] is True

    def test_authenticated_includes_shortcuts_preferences(self, authenticated_request):
        shortcuts_preferences = {"applyUpdates": "l"}
        authenticated_request.user.shortcuts_preferences = shortcuts_preferences

        preferences = session.model(authenticated_request)["preferences"]

        assert preferences["shortcuts_preferences"] == shortcuts_preferences

    def test_authenticated_omits_shortcuts_preferences_when_none(
        self, authenticated_request
    ):
        authenticated_request.user.shortcuts_preferences = None

        preferences = session.model(authenticated_request)["preferences"]

        assert "shortcuts_preferences" not in preferences


class TestProfile:
    def test_userid_unauthenticated(self, unauthenticated_request):
        assert session.profile(unauthenticated_request)["userid"] is None

    def test_userid_authenticated(self, authenticated_request):
        profile = session.profile(authenticated_request)
        assert profile["userid"] == "acct:user@example.com"

    def test_proxies_group_lookup_to_service(self, authenticated_request):
        svc = authenticated_request.find_service(name="group_list")

        session.profile(authenticated_request)

        svc.session_groups.assert_called_once_with(
            user=authenticated_request.user,
            authority=authenticated_request.default_authority,
        )

    def test_proxies_group_lookup_to_service_for_unauth(self, unauthenticated_request):
        svc = unauthenticated_request.find_service(name="group_list")

        session.profile(unauthenticated_request)

        svc.session_groups.assert_called_once_with(
            authority=unauthenticated_request.default_authority, user=None
        )

    def test_open_group_is_public(self, unauthenticated_request, world_group):
        svc = unauthenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [world_group]

        profile = session.profile(unauthenticated_request)

        assert profile["groups"][0]["public"]

    def test_private_group_is_not_public(self, authenticated_request, factories):
        a_group = factories.Group()
        svc = authenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [a_group]

        profile = session.profile(authenticated_request)

        assert not profile["groups"][0]["public"]

    def test_open_group_has_no_url(self, unauthenticated_request, world_group):
        svc = unauthenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [world_group]

        profile = session.profile(unauthenticated_request)

        assert not profile["groups"][0].get("url")

    def test_private_group_has_url(self, authenticated_request, factories):
        a_group = factories.Group()
        svc = authenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [a_group]

        profile = session.profile(authenticated_request)

        assert profile["groups"][0]["url"]

    def test_includes_features(self, authenticated_request):
        feature_dict = {"feature_one": True, "feature_two": False}
        authenticated_request.set_features(feature_dict)

        assert session.profile(authenticated_request)["features"] == feature_dict

    def test_anonymous_hides_sidebar_tutorial(self, unauthenticated_request):
        preferences = session.profile(unauthenticated_request)["preferences"]

        assert "show_sidebar_tutorial" not in preferences

    @pytest.mark.parametrize("dismissed", [True, False])
    def test_authenticated_sidebar_tutorial(self, authenticated_request, dismissed):
        authenticated_request.set_sidebar_tutorial_dismissed(dismissed)

        preferences = session.profile(authenticated_request)["preferences"]

        if dismissed:
            assert "show_sidebar_tutorial" not in preferences
        else:
            assert preferences["show_sidebar_tutorial"] is True

    def test_anonymous_hides_youtube_gdpr_banner(self, unauthenticated_request):
        preferences = session.profile(unauthenticated_request)["preferences"]

        assert "show_youtube_gdpr_banner" not in preferences

    @pytest.mark.parametrize("dismissed", [True, False])
    def test_authenticated_youtube_gdpr_banner(self, authenticated_request, dismissed):
        authenticated_request.set_youtube_gdpr_banner_dismissed(dismissed)

        preferences = session.profile(authenticated_request)["preferences"]

        if dismissed:
            assert "show_youtube_gdpr_banner" not in preferences
        else:
            assert preferences["show_youtube_gdpr_banner"] is True

    def test_anonymous_hides_instructor_survey(self, unauthenticated_request):
        preferences = session.profile(unauthenticated_request)["preferences"]

        assert "show_instructor_survey" not in preferences

    def test_instructor_survey_shown_when_unanswered(self, authenticated_request):
        authenticated_request.set_edu_role_survey(None)

        preferences = session.profile(authenticated_request)["preferences"]

        assert preferences["show_instructor_survey"] is True

    @pytest.mark.parametrize("response", ["instructor", "not_instructor", "dismissed"])
    def test_instructor_survey_hidden_once_answered(
        self, authenticated_request, response
    ):
        # All three are answers. "not_instructor" and "dismissed" must stop us
        # asking again just like "instructor" does, which is why the check is
        # for NULL rather than for falsiness.
        authenticated_request.set_edu_role_survey(response)

        preferences = session.profile(authenticated_request)["preferences"]

        assert "show_instructor_survey" not in preferences

    def test_instructor_survey_hidden_when_flag_is_off(self, authenticated_request):
        # The flag is the kill switch: with it off, h must stop sending the
        # preference, rather than leaving it to the client to ignore it.
        authenticated_request.set_edu_role_survey(None)
        authenticated_request.set_features({"instructor_survey": False})

        preferences = session.profile(authenticated_request)["preferences"]

        assert "show_instructor_survey" not in preferences

    def test_instructor_survey_hidden_for_non_edu_email(self, authenticated_request):
        authenticated_request.set_edu_role_survey(None, email="someone@gmail.com")

        preferences = session.profile(authenticated_request)["preferences"]

        assert "show_instructor_survey" not in preferences

    def test_instructor_survey_hidden_for_third_party_authority(
        self, authority, fake_feature
    ):
        # The survey is for web app users only, and this holds even with the
        # flag on for this user — which is what enabling it for `everyone`
        # amounts to — because the authority is checked here rather than left
        # to the flag.
        request = FakeRequest(
            authority, "acct:someone@thirdparty.com", "thirdparty.com", fake_feature
        )
        request.set_features({"instructor_survey": True})
        request.set_edu_role_survey(None)

        preferences = session.profile(request)["preferences"]

        assert "show_instructor_survey" not in preferences

    def test_authenticated_includes_shortcuts_preferences(self, authenticated_request):
        shortcuts_preferences = {"applyUpdates": "l"}
        authenticated_request.user.shortcuts_preferences = shortcuts_preferences

        preferences = session.profile(authenticated_request)["preferences"]

        assert preferences["shortcuts_preferences"] == shortcuts_preferences

    def test_authenticated_omits_shortcuts_preferences_when_none(
        self, authenticated_request
    ):
        authenticated_request.user.shortcuts_preferences = None

        preferences = session.profile(authenticated_request)["preferences"]

        assert "shortcuts_preferences" not in preferences

    def test_anonymous_authority(self, unauthenticated_request, authority):
        assert session.profile(unauthenticated_request)["authority"] == authority

    def test_authority_override(self, unauthenticated_request):
        profile = session.profile(unauthenticated_request, "foo.com")

        assert profile["authority"] == "foo.com"

    def test_authenticated_authority(self, authenticated_request, authority):
        assert session.profile(authenticated_request)["authority"] == authority

    def test_authenticated_ignores_authority_override(
        self, authenticated_request, authority
    ):
        profile = session.profile(authenticated_request, "foo.com")

        assert profile["authority"] == authority

    def test_third_party_authority(self, third_party_request, third_party_domain):
        assert session.profile(third_party_request)["authority"] == third_party_domain

    def test_third_party_ingores_authority_override(
        self, third_party_request, third_party_domain
    ):
        profile = session.profile(third_party_request, "foo.com")

        assert profile["authority"] == third_party_domain

    def test_user_info_authenticated(self, authenticated_request):
        profile = session.profile(authenticated_request)
        user_info = profile["user_info"]
        assert user_info["display_name"] == authenticated_request.user.display_name

    def test_user_info_unauthenticated(self, unauthenticated_request):
        profile = session.profile(unauthenticated_request)
        assert "user_info" not in profile

    @pytest.fixture
    def third_party_domain(self):
        return "thirdparty.example.org"

    @pytest.fixture
    def third_party_request(self, authority, third_party_domain, fake_feature):
        return FakeRequest(
            authority,
            f"acct:user@{third_party_domain}",
            third_party_domain,
            fake_feature,
        )


class TestProfileWithScopedGroups:
    def test_proxies_group_lookup_to_service(self, authenticated_request):
        svc = authenticated_request.find_service(name="group_list")

        session.profile(authenticated_request)

        svc.session_groups.assert_called_once_with(
            user=authenticated_request.user,
            authority=authenticated_request.default_authority,
        )

    def test_proxies_group_lookup_to_service_for_unauth(self, unauthenticated_request):
        svc = unauthenticated_request.find_service(name="group_list")

        session.profile(unauthenticated_request)

        svc.session_groups.assert_called_once_with(
            authority=unauthenticated_request.default_authority, user=None
        )

    def test_private_group_is_not_public(self, authenticated_request, factories):
        a_group = factories.Group()
        svc = authenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [a_group]

        profile = session.profile(authenticated_request)

        assert not profile["groups"][0]["public"]

    def test_private_group_has_url(self, authenticated_request, factories):
        a_group = factories.Group()
        svc = authenticated_request.find_service(name="group_list")
        svc.session_groups.return_value = [a_group]

        profile = session.profile(authenticated_request)

        assert profile["groups"][0]["url"]


class TestUserInfo:
    def test_returns_user_info_object(self, factories):
        user = factories.User.build(display_name="Jane Doe")

        result = session.user_info(user)
        assert result == {"user_info": {"display_name": "Jane Doe"}}

    def test_allows_null_display_name(self, factories):
        user = factories.User.build(display_name=None)

        result = session.user_info(user)
        assert result == {"user_info": {"display_name": None}}

    def test_format_returns_empty_dict_when_user_missing(self):
        assert not session.user_info(None)


class FakeRequest:
    def __init__(self, authority, userid, user_authority, fake_feature):
        self.default_authority = authority
        self.authenticated_userid = userid

        if userid is None:
            self.user = None
        else:
            # `email` and `edu_role_survey_response` are spelled out rather
            # than left to Mock's auto-attributes: the EDU survey reads both,
            # and a Mock stands in for a real value well enough to hide a
            # missing one. Defaults say "no email, never answered", so the
            # survey is off until a test asks for it via set_edu_role_survey.
            self.user = mock.Mock(
                groups=[],
                authority=user_authority,
                email=None,
                edu_role_survey_response=None,
            )

        self.feature = fake_feature
        self.route_url = mock.Mock(return_value="/group/a")
        self.session = mock.Mock()

        self._group_list_service = mock.create_autospec(
            GroupListService, spec_set=True, instance=True
        )

    def set_features(self, feature_dict):
        self.feature.flags = feature_dict

    def set_sidebar_tutorial_dismissed(self, dismissed):
        self.user.sidebar_tutorial_dismissed = dismissed

    def set_youtube_gdpr_banner_dismissed(self, dismissed):
        self.user.youtube_gdpr_banner_dismissed = dismissed

    def set_edu_role_survey(self, response, email="someone@stanford.edu"):
        self.user.edu_role_survey_response = response
        self.user.email = email

    def find_service(self, **kwargs):
        return {"group_list": self._group_list_service}[kwargs["name"]]


@pytest.fixture
def authority():
    return "example.com"


@pytest.fixture
def unauthenticated_request(authority, fake_feature):
    return FakeRequest(authority, None, None, fake_feature)


@pytest.fixture
def authenticated_request(authority, fake_feature):
    return FakeRequest(authority, f"acct:user@{authority}", authority, fake_feature)


@pytest.fixture
def world_group(factories):
    return factories.OpenGroup(name="Public", pubid="__worldish__")
