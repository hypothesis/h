from unittest.mock import sentinel

import pytest

from h.security.policy.top_level import TopLevelPolicy, get_subpolicy


class TestTopLevelPolicy:
    def test_forget(self, get_subpolicy, policy, pyramid_request):
        headers = policy.forget(pyramid_request, foo="bar")

        get_subpolicy.return_value.forget.assert_called_once_with(
            pyramid_request, foo="bar"
        )
        assert headers == get_subpolicy.return_value.forget.return_value

    def test_identity(self, get_subpolicy, policy, pyramid_request):
        identity = policy.identity(pyramid_request)

        get_subpolicy.return_value.identity.assert_called_once_with(pyramid_request)
        assert identity == get_subpolicy.return_value.identity.return_value

    def test_remember(self, get_subpolicy, policy, pyramid_request):
        headers = policy.remember(pyramid_request, sentinel.userid, foo="bar")

        get_subpolicy.return_value.remember.assert_called_once_with(
            pyramid_request, sentinel.userid, foo="bar"
        )
        assert headers == get_subpolicy.return_value.remember.return_value

    @pytest.fixture
    def policy(self):
        return TopLevelPolicy()

    @pytest.fixture(autouse=True)
    def get_subpolicy(self, mocker):
        return mocker.patch("h.security.policy.top_level.get_subpolicy", autospec=True)


class TestGetSubpolicy:
    def test_api_request(
        self,
        is_api_request,
        pyramid_request,
        AuthClientPolicy,
        APICookiePolicy,
        APIPolicy,
        BearerTokenPolicy,
        CookiePolicy,
    ):
        is_api_request.return_value = True

        policy = get_subpolicy(pyramid_request)

        BearerTokenPolicy.assert_called_once_with()
        AuthClientPolicy.assert_called_once_with()
        CookiePolicy.assert_called_once_with()
        APICookiePolicy.assert_called_once_with(CookiePolicy.return_value)
        APIPolicy.assert_called_once_with(
            [
                BearerTokenPolicy.return_value,
                AuthClientPolicy.return_value,
                APICookiePolicy.return_value,
            ]
        )
        assert policy == APIPolicy.return_value

    def test_non_api_request(self, is_api_request, pyramid_request, CookiePolicy):
        is_api_request.return_value = False

        policy = get_subpolicy(pyramid_request)

        CookiePolicy.assert_called_once_with()
        assert policy == CookiePolicy.return_value


@pytest.fixture(autouse=True)
def is_api_request(mocker):
    return mocker.patch("h.security.policy.top_level.is_api_request", autospec=True)


@pytest.fixture(autouse=True)
def AuthClientPolicy(mocker):
    return mocker.patch("h.security.policy.top_level.AuthClientPolicy", autospec=True)


@pytest.fixture(autouse=True)
def APICookiePolicy(mocker):
    return mocker.patch("h.security.policy.top_level.APICookiePolicy", autospec=True)


@pytest.fixture(autouse=True)
def APIPolicy(mocker):
    return mocker.patch("h.security.policy.top_level.APIPolicy", autospec=True)


@pytest.fixture(autouse=True)
def BearerTokenPolicy(mocker):
    return mocker.patch("h.security.policy.top_level.BearerTokenPolicy", autospec=True)


@pytest.fixture(autouse=True)
def CookiePolicy(mocker):
    return mocker.patch("h.security.policy.top_level.CookiePolicy", autospec=True)
