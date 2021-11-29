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
            self.user = mock.Mock(groups=[], authority=user_authority)

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
