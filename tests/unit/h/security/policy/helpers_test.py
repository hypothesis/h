from unittest.mock import create_autospec, sentinel

import pytest
from webob.cookies import SignedCookieProfile

from h.security.policy.helpers import AuthTicketCookieHelper, is_api_request


class TestIsAPIRequest:
    @pytest.mark.parametrize(
        "route_name,expected_result",
        [
            ("anything", False),
            ("api.anything", True),
        ],
    )
    def test_it(self, pyramid_request, route_name, expected_result):
        pyramid_request.matched_route.name = route_name

        assert is_api_request(pyramid_request) == expected_result

    def test_it_when_matched_route_is_None(self, pyramid_request):
        pyramid_request.matched_route = None

        assert is_api_request(pyramid_request) is False


class TestAuthTicketCookieHelper:
    def test_identity(
        self, auth_ticket_service, cookie, helper, pyramid_request, Identity
    ):
        ticket = auth_ticket_service.verify_ticket.return_value
        user = ticket.user
        user.deleted = False

        result = helper.identity(cookie, pyramid_request)

        auth_ticket_service.verify_ticket.assert_called_once_with(
            sentinel.userid, sentinel.ticket_id
        )
        Identity.from_models.assert_called_once_with(user=user)
        assert result == (Identity.from_models.return_value, ticket)

    def test_identity_when_no_user(
        self, auth_ticket_service, cookie, helper, pyramid_request
    ):
        auth_ticket_service.verify_ticket.return_value = None

        assert helper.identity(cookie, pyramid_request) == (None, None)

    def test_identity_when_user_deleted(
        self, auth_ticket_service, cookie, helper, pyramid_request
    ):
        auth_ticket_service.verify_ticket.return_value.user.deleted = True

        assert helper.identity(cookie, pyramid_request) == (None, None)

    def test_add_ticket(self, helper, auth_ticket_service, pyramid_request, AuthTicket):
        auth_ticket = helper.add_ticket(pyramid_request, sentinel.userid)

        AuthTicket.generate_ticket_id.assert_called_once_with()
        auth_ticket_service.add_ticket.assert_called_once_with(
            sentinel.userid, AuthTicket.generate_ticket_id.return_value
        )
        assert auth_ticket == auth_ticket_service.add_ticket.return_value

    def test_remember(self, cookie, helper, factories):
        auth_ticket = factories.AuthTicket()

        headers = helper.remember(cookie, sentinel.userid, auth_ticket)

        cookie.get_headers.assert_called_once_with([sentinel.userid, auth_ticket.id])
        assert headers == cookie.get_headers.return_value

    def test_forget(self, auth_ticket_service, cookie, helper, pyramid_request):
        headers = helper.forget(cookie, pyramid_request)

        auth_ticket_service.remove_ticket.assert_called_once_with(sentinel.ticket_id)
        cookie.get_headers.assert_called_once_with(None, max_age=0)
        assert headers == cookie.get_headers.return_value

    def test_forget_when_no_ticket_id(
        self, auth_ticket_service, cookie, helper, pyramid_request
    ):
        cookie.get_value.return_value = None

        headers = helper.forget(cookie, pyramid_request)

        auth_ticket_service.remove_ticket.assert_not_called()
        cookie.get_headers.assert_called_once_with(None, max_age=0)
        assert headers == cookie.get_headers.return_value

    @pytest.mark.parametrize(
        "vary,expected_vary",
        (
            (None, ["Cookie"]),
            (["Cookie"], ["Cookie"]),
            (["Other"], ["Cookie", "Other"]),
        ),
    )
    def test_add_vary_by_cookie(self, pyramid_request, vary, expected_vary):
        pyramid_request.response.vary = vary

        AuthTicketCookieHelper.add_vary_by_cookie(pyramid_request)

        assert len(pyramid_request.response_callbacks) == 1
        callback = pyramid_request.response_callbacks[0]
        callback(pyramid_request, pyramid_request.response)
        assert sorted(pyramid_request.response.vary) == sorted(expected_vary)

    @pytest.mark.parametrize(
        "value,expected_result",
        [
            (None, (None, None)),
            (
                (sentinel.userid, sentinel.ticket_id),
                (sentinel.userid, sentinel.ticket_id),
            ),
        ],
    )
    def test_get_cookie_value(self, cookie, value, expected_result):
        cookie.get_value.return_value = value

        assert AuthTicketCookieHelper.get_cookie_value(cookie) == expected_result

    @pytest.fixture
    def cookie(self):
        cookie = create_autospec(SignedCookieProfile, instance=True, spec_set=True)
        cookie.get_value.return_value = (sentinel.userid, sentinel.ticket_id)
        return cookie

    @pytest.fixture
    def helper(self):
        return AuthTicketCookieHelper()


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy.helpers.Identity", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def AuthTicket(mocker):
    return mocker.patch(
        "h.security.policy.helpers.AuthTicket", autospec=True, spec_set=True
    )
