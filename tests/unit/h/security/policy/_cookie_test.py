from unittest.mock import create_autospec, sentinel

import pytest

from h.security.policy._cookie import CookiePolicy
from h.security.policy.helpers import AuthTicketCookieHelper


class TestCookiePolicy:
    def test_identity(self, cookie_policy, helper, pyramid_request):
        identity = cookie_policy.identity(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_request)
        assert identity == helper.identity.return_value

    def test_authenticated_userid(
        self, cookie_policy, helper, pyramid_request, Identity
    ):
        authenticated_userid = cookie_policy.authenticated_userid(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_request)
        Identity.authenticated_userid.assert_called_once_with(
            helper.identity.return_value
        )
        assert authenticated_userid == Identity.authenticated_userid.return_value

    def test_remember(self, cookie_policy, helper, pyramid_request):
        pyramid_request.session["data"] = "old"

        headers = cookie_policy.remember(pyramid_request, sentinel.userid, foo="bar")

        assert not pyramid_request.session
        helper.remember.assert_called_once_with(
            sentinel.cookie, pyramid_request, sentinel.userid
        )
        assert headers == helper.remember.return_value

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

    def test_forget(self, cookie_policy, helper, pyramid_request):
        headers = cookie_policy.forget(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.forget.assert_called_once_with(sentinel.cookie, pyramid_request)
        assert headers == helper.forget.return_value

    def test_permits(self, cookie_policy, helper, pyramid_request, identity_permits):
        permits = cookie_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_request)
        identity_permits.assert_called_once_with(
            helper.identity.return_value, sentinel.context, sentinel.permission
        )
        assert permits == identity_permits.return_value

    @pytest.fixture
    def helper(self):
        return create_autospec(AuthTicketCookieHelper, instance=True, spec_set=True)

    @pytest.fixture
    def cookie_policy(self, helper):
        return CookiePolicy(sentinel.cookie, helper)


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
