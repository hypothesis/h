from unittest.mock import call, create_autospec, sentinel

import pytest
from webob.cookies import SignedCookieProfile

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

    def test_authenticated_userid(self, get_subpolicy, policy, pyramid_request):
        authenticated_userid = policy.authenticated_userid(pyramid_request)

        get_subpolicy.return_value.authenticated_userid.assert_called_once_with(
            pyramid_request
        )
        assert (
            authenticated_userid
            == get_subpolicy.return_value.authenticated_userid.return_value
        )

    def test_remember(self, get_subpolicy, policy, pyramid_request):
        headers = policy.remember(pyramid_request, sentinel.userid, foo="bar")

        get_subpolicy.return_value.remember.assert_called_once_with(
            pyramid_request, sentinel.userid, foo="bar"
        )
        assert headers == get_subpolicy.return_value.remember.return_value

    def test_permits(self, get_subpolicy, policy, pyramid_request):
        permits = policy.permits(pyramid_request, sentinel.context, sentinel.permission)

        get_subpolicy.return_value.permits.assert_called_once_with(
            pyramid_request, sentinel.context, sentinel.permission
        )
        assert permits == get_subpolicy.return_value.permits.return_value

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
        webob,
        AuthTicketCookieHelper,
    ):
        is_api_request.return_value = True
        api_authcookie = create_autospec(
            SignedCookieProfile, instance=True, spec_set=True
        )
        webob.cookies.SignedCookieProfile.return_value = api_authcookie

        policy = get_subpolicy(pyramid_request)

        BearerTokenPolicy.assert_called_once_with()
        AuthClientPolicy.assert_called_once_with()
        assert webob.cookies.SignedCookieProfile.call_args_list == [
            call(
                secret="test_h_api_auth_cookie_secret",
                salt="test_h_api_auth_cookie_salt",
                cookie_name="h_api_authcookie.v2",
                max_age=31539600,
                httponly=True,
                secure=True,
                samesite="strict",
            )
        ]
        api_authcookie.bind.assert_called_once_with(pyramid_request)
        AuthTicketCookieHelper.assert_called_once_with()
        APICookiePolicy.assert_called_once_with(
            api_authcookie.bind.return_value,
            AuthTicketCookieHelper.return_value,
        )
        APIPolicy.assert_called_once_with(
            [
                BearerTokenPolicy.return_value,
                AuthClientPolicy.return_value,
                APICookiePolicy.return_value,
            ]
        )
        assert policy == APIPolicy.return_value

    def test_non_api_request(
        self,
        is_api_request,
        pyramid_request,
        CookiePolicy,
        webob,
        AuthTicketCookieHelper,
    ):
        is_api_request.return_value = False
        html_authcookie = create_autospec(
            SignedCookieProfile, instance=True, spec_set=True
        )
        api_authcookie = create_autospec(
            SignedCookieProfile, instance=True, spec_set=True
        )
        webob.cookies.SignedCookieProfile.side_effect = [
            api_authcookie,
            html_authcookie,
        ]

        policy = get_subpolicy(pyramid_request)

        assert webob.cookies.SignedCookieProfile.call_args_list == [
            call(
                secret="test_h_api_auth_cookie_secret",
                salt="test_h_api_auth_cookie_salt",
                cookie_name="h_api_authcookie.v2",
                max_age=31539600,
                httponly=True,
                secure=True,
                samesite="strict",
            ),
            call(
                secret="test_h_auth_cookie_secret",
                salt="authsanity",
                cookie_name="auth",
                max_age=31536000,
                httponly=True,
                secure=True,
            ),
        ]
        api_authcookie.bind.assert_called_once_with(pyramid_request)
        html_authcookie.bind.assert_called_once_with(pyramid_request)
        AuthTicketCookieHelper.assert_called_once_with()
        CookiePolicy.assert_called_once_with(
            html_authcookie.bind.return_value,
            api_authcookie.bind.return_value,
            AuthTicketCookieHelper.return_value,
        )
        assert policy == CookiePolicy.return_value


@pytest.fixture(autouse=True)
def is_api_request(mocker):
    return mocker.patch("h.security.policy.top_level.is_api_request", autospec=True)


@pytest.fixture(autouse=True)
def AuthClientPolicy(mocker):
    return mocker.patch("h.security.policy.top_level.AuthClientPolicy", autospec=True)


@pytest.fixture(autouse=True)
def AuthTicketCookieHelper(mocker):
    return mocker.patch(
        "h.security.policy.top_level.AuthTicketCookieHelper", autospec=True
    )


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


@pytest.fixture
def pyramid_settings(pyramid_settings):
    pyramid_settings["h_auth_cookie_secret"] = "test_h_auth_cookie_secret"
    pyramid_settings["h_api_auth_cookie_secret"] = "test_h_api_auth_cookie_secret"
    pyramid_settings["h_api_auth_cookie_salt"] = "test_h_api_auth_cookie_salt"
    return pyramid_settings


@pytest.fixture(autouse=True)
def webob(mocker):
    return mocker.patch(
        "h.security.policy.top_level.webob", autospec=True, spec_set=True
    )
