from unittest.mock import create_autospec, sentinel

import pytest
import webob
from h_matchers import Any

from h.security.policy import _cookie
from h.security.policy._cookie import CookiePolicy, base64


@pytest.mark.usefixtures("auth_ticket_service")
class TestCookiePolicy:
    def test_identity(
        self, pyramid_request, auth_ticket_service, cookie_policy, user, Identity
    ):
        identity = cookie_policy.identity(pyramid_request)

        auth_ticket_service.verify_ticket.assert_called_once_with(
            user.userid, sentinel.ticket_id
        )
        Identity.from_models.assert_called_once_with(
            user=auth_ticket_service.verify_ticket.return_value
        )
        assert identity == Identity.from_models.return_value

    def test_identity_when_user_marked_as_deleted(
        self, pyramid_request, auth_ticket_service, cookie_policy
    ):
        auth_ticket_service.verify_ticket.return_value.deleted = True

        assert cookie_policy.identity(pyramid_request) is None

    def test_identity_with_no_auth_ticket(
        self, pyramid_request, auth_ticket_service, cookie_policy
    ):
        auth_ticket_service.verify_ticket.return_value = None

        assert cookie_policy.identity(pyramid_request) is None

    def test_authenticated_userid(
        self, pyramid_request, cookie_policy, Identity, mocker
    ):
        mocker.spy(cookie_policy, "identity")

        authenticated_userid = cookie_policy.authenticated_userid(pyramid_request)

        cookie_policy.identity.assert_called_once_with(pyramid_request)
        Identity.authenticated_userid.assert_called_once_with(
            cookie_policy.identity.spy_return
        )
        assert authenticated_userid == Identity.authenticated_userid.return_value

    def test_remember(
        self,
        pyramid_request,
        auth_ticket_service,
        user,
        cookie,
        cookie_policy,
        urlsafe_b64encode,
        urandom,
    ):
        pyramid_request.session["data"] = "old"
        auth_ticket_service.verify_ticket.return_value = user

        result = cookie_policy.remember(pyramid_request, sentinel.userid)

        # The `pyramid.testing.DummySession` is a dict so this is the closest
        # we can get to saying it's been invalidated
        assert not pyramid_request.session
        urandom.assert_called_once_with(32)
        urlsafe_b64encode.assert_called_once_with(urandom.spy_return)
        ticket_id = urlsafe_b64encode.spy_return.rstrip(b"=").decode("ascii")
        auth_ticket_service.add_ticket.assert_called_once_with(
            sentinel.userid, ticket_id
        )
        cookie.get_headers.assert_called_once_with([sentinel.userid, ticket_id])
        assert result == cookie.get_headers.return_value

    def test_remember_with_existing_user(
        self, pyramid_request, user, cookie_policy, Identity
    ):
        pyramid_request.session["data"] = "old"
        # This is a secret parameter used by `pyramid.testing.DummySession`
        pyramid_request.session["_csrft_"] = "old_csrf_token"
        Identity.authenticated_userid.return_value = user.userid

        cookie_policy.remember(pyramid_request, user.userid)

        assert pyramid_request.session["data"] == "old"
        assert pyramid_request.session["_csrft_"] != "old_csrf_token"

    def test_forget(self, pyramid_request, auth_ticket_service, cookie_policy, cookie):
        pyramid_request.session["data"] = "old"

        result = cookie_policy.forget(pyramid_request)

        # The `pyramid.testing.DummySession` is a dict so this is the closest
        # we can get to saying it's been invalidated
        assert not pyramid_request.session
        auth_ticket_service.remove_ticket.assert_called_once_with(sentinel.ticket_id)
        cookie.get_headers.assert_called_once_with(None, max_age=0)
        assert result == cookie.get_headers.return_value

    def test_forget_when_no_ticket_id_in_cookie(
        self, auth_ticket_service, cookie, cookie_policy, pyramid_request
    ):
        cookie.get_value.return_value = None

        result = cookie_policy.forget(pyramid_request)

        assert not pyramid_request.session
        auth_ticket_service.remove_ticket.assert_not_called()
        cookie.get_headers.assert_called_once_with(None, max_age=0)
        assert result == cookie.get_headers.return_value

    def test_permits(self, cookie_policy, pyramid_request, mocker, identity_permits):
        mocker.spy(cookie_policy, "identity")

        result = cookie_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        cookie_policy.identity.assert_called_once_with(pyramid_request)
        identity_permits.assert_called_once_with(
            cookie_policy.identity.spy_return, sentinel.context, sentinel.permission
        )
        assert result == identity_permits.return_value

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
        self, pyramid_request, method, args, vary, expected_vary, cookie_policy
    ):
        pyramid_request.response.vary = vary
        getattr(cookie_policy, method)(pyramid_request, *args)

        assert len(pyramid_request.response_callbacks) == 1
        callback = pyramid_request.response_callbacks[0]

        callback(pyramid_request, pyramid_request.response)

        assert (
            pyramid_request.response.vary
            == Any.iterable.containing(expected_vary).only()
        )

    @pytest.fixture
    def cookie(self, user):
        cookie = create_autospec(
            webob.cookies.SignedCookieProfile, instance=True, spec_set=True
        )
        cookie.get_value.return_value = (user.userid, sentinel.ticket_id)
        return cookie

    @pytest.fixture
    def cookie_policy(self, cookie):
        return CookiePolicy(cookie)

    @pytest.fixture
    def user(self, factories):
        return factories.User()


@pytest.fixture(autouse=True)
def urlsafe_b64encode(mocker):
    return mocker.spy(base64, "urlsafe_b64encode")


@pytest.fixture(autouse=True)
def urandom(mocker):
    return mocker.spy(_cookie, "urandom")


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
