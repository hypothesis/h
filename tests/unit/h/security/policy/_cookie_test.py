from unittest.mock import call, create_autospec, sentinel

import pytest
from webob.cookies import SignedCookieProfile

from h.security.policy._cookie import CookiePolicy
from h.security.policy.helpers import AuthTicketCookieHelper


class TestCookiePolicy:
    def test_identity(self, cookie_policy, helper, pyramid_request, html_authcookie):
        identity = cookie_policy.identity(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(html_authcookie, pyramid_request)
        assert identity == helper.identity.return_value

    def test_authenticated_userid(
        self, cookie_policy, helper, pyramid_request, Identity, html_authcookie
    ):
        authenticated_userid = cookie_policy.authenticated_userid(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(html_authcookie, pyramid_request)
        Identity.authenticated_userid.assert_called_once_with(
            helper.identity.return_value
        )
        assert authenticated_userid == Identity.authenticated_userid.return_value

    def test_remember(
        self, cookie_policy, html_authcookie, api_authcookie, helper, pyramid_request
    ):
        pyramid_request.session["data"] = "old"

        def remember(cookie, *_args, **_kwargs):
            if cookie == html_authcookie:
                return [
                    sentinel.html_authcookie_header_1,
                    sentinel.html_authcookie_header_2,
                ]
            if cookie == api_authcookie:
                return [
                    sentinel.api_authcookie_header_1,
                    sentinel.api_authcookie_header_2,
                ]

            assert False, "Should never reach here"  # pragma: no cover

        helper.remember.side_effect = remember

        headers = cookie_policy.remember(pyramid_request, sentinel.userid, foo="bar")

        assert not pyramid_request.session
        assert helper.remember.call_args_list == [
            call(html_authcookie, pyramid_request, sentinel.userid),
            call(api_authcookie, pyramid_request, sentinel.userid),
        ]
        assert headers == [
            sentinel.html_authcookie_header_1,
            sentinel.html_authcookie_header_2,
            sentinel.api_authcookie_header_1,
            sentinel.api_authcookie_header_2,
        ]

    def test_remember_with_existing_user(
        self, cookie_policy, pyramid_request, factories, Identity
    ):
        user = factories.User()
        pyramid_request.session["data"] = "old"
        # This is a secret parameter used by `pyramid.testing.DummySession`
        pyramid_request.session["_csrft_"] = "old_csrf_token"
        Identity.authenticated_userid.return_value = user.userid

        cookie_policy.remember(pyramid_request, user.userid, foo="bar")

        assert pyramid_request.session["data"] == "old"
        assert pyramid_request.session["_csrft_"] != "old_csrf_token"

    def test_forget(
        self, cookie_policy, helper, pyramid_request, html_authcookie, api_authcookie
    ):
        def forget(cookie, *_args, **_kwargs):
            if cookie == html_authcookie:
                return [
                    sentinel.html_authcookie_header_1,
                    sentinel.html_authcookie_header_2,
                ]
            if cookie == api_authcookie:
                return [
                    sentinel.api_authcookie_header_1,
                    sentinel.api_authcookie_header_2,
                ]

            assert False, "Should never reach here"  # pragma: no cover

        helper.forget.side_effect = forget

        headers = cookie_policy.forget(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        assert helper.forget.call_args_list == [
            call(html_authcookie, pyramid_request),
            call(api_authcookie, pyramid_request),
        ]
        assert headers == [
            sentinel.html_authcookie_header_1,
            sentinel.html_authcookie_header_2,
            sentinel.api_authcookie_header_1,
            sentinel.api_authcookie_header_2,
        ]

    def test_permits(
        self, cookie_policy, helper, pyramid_request, identity_permits, html_authcookie
    ):
        permits = cookie_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(html_authcookie, pyramid_request)
        identity_permits.assert_called_once_with(
            helper.identity.return_value, sentinel.context, sentinel.permission
        )
        assert permits == identity_permits.return_value

    @pytest.fixture
    def html_authcookie(self, pyramid_request):
        html_authcookie = SignedCookieProfile("secret", "salt", cookie_name="auth")
        pyramid_request.cookies[html_authcookie.cookie_name] = html_authcookie
        return html_authcookie.bind(pyramid_request)

    @pytest.fixture
    def api_authcookie(self, pyramid_request):
        api_authcookie = SignedCookieProfile(
            "secret", "salt", cookie_name="h_api_authcookie"
        )

        return api_authcookie.bind(pyramid_request)

    @pytest.fixture
    def helper(self):
        return create_autospec(AuthTicketCookieHelper, instance=True, spec_set=True)

    @pytest.fixture
    def cookie_policy(self, html_authcookie, api_authcookie, helper):
        return CookiePolicy(html_authcookie, api_authcookie, helper)


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy._cookie.Identity", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def identity_permits(mocker):
    return mocker.patch(
        "h.security.policy._cookie.identity_permits", autospec=True, spec_set=True
    )
