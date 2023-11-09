from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.security import Identity
from h.security.policy._cookie import CookiePolicy


@pytest.mark.usefixtures("auth_cookie_service")
class TestCookiePolicy:
    def test_identity(self, pyramid_request, auth_cookie_service):
        identity = CookiePolicy().identity(pyramid_request)

        auth_cookie_service.verify_cookie.assert_called_once()
        assert identity == Identity.from_models(
            user=auth_cookie_service.verify_cookie.return_value
        )

    def test_identity_with_no_cookie(self, pyramid_request, auth_cookie_service):
        auth_cookie_service.verify_cookie.return_value = None

        assert CookiePolicy().identity(pyramid_request) is None

    def test_remember(self, pyramid_request, auth_cookie_service, user):
        pyramid_request.session["data"] = "old"
        auth_cookie_service.verify_cookie.return_value = user

        result = CookiePolicy().remember(pyramid_request, sentinel.userid)

        # The `pyramid.testing.DummySession` is a dict so this is the closest
        # we can get to saying it's been invalidated
        assert not pyramid_request.session
        auth_cookie_service.create_cookie.assert_called_once_with(sentinel.userid)
        assert result == auth_cookie_service.create_cookie.return_value

    def test_remember_with_existing_user(
        self, pyramid_request, auth_cookie_service, user
    ):
        pyramid_request.session["data"] = "old"
        # This is a secret parameter used by `pyramid.testing.DummySession`
        pyramid_request.session["_csrft_"] = "old_csrf_token"
        auth_cookie_service.verify_cookie.return_value = user

        CookiePolicy().remember(pyramid_request, user.userid)

        assert pyramid_request.session["data"] == "old"
        assert pyramid_request.session["_csrft_"] != "old_csrf_token"

    def test_forget(self, pyramid_request, auth_cookie_service):
        pyramid_request.session["data"] = "old"

        result = CookiePolicy().forget(pyramid_request)

        # The `pyramid.testing.DummySession` is a dict so this is the closest
        # we can get to saying it's been invalidated
        assert not pyramid_request.session
        auth_cookie_service.revoke_cookie.assert_called_once_with()
        assert result == auth_cookie_service.revoke_cookie.return_value

    @pytest.mark.parametrize(
        "method,args",
        (("identity", ()), ("remember", (sentinel.userid,)), ("forget", ())),
    )
    @pytest.mark.parametrize(
        "vary,expected_vary",
        (
            (None, ["Cookie"]),
            (["Cookie"], ["Cookie"]),
            (["Other"], ["Cookie", "Other"]),
        ),
    )
    def test_methods_add_vary_callback(
        self, pyramid_request, method, args, vary, expected_vary
    ):
        pyramid_request.response.vary = vary
        getattr(CookiePolicy(), method)(pyramid_request, *args)

        assert len(pyramid_request.response_callbacks) == 1
        callback = pyramid_request.response_callbacks[0]

        callback(pyramid_request, pyramid_request.response)

        assert (
            pyramid_request.response.vary
            == Any.iterable.containing(expected_vary).only()
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()
