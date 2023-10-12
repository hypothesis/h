from datetime import datetime, timedelta
from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any
from webob.cookies import SignedCookieProfile

from h.models import AuthTicket
from h.services.auth_cookie import AuthCookieService, factory


def assert_nearly_equal(first_date, second_date):
    diff = abs(first_date - second_date)

    assert diff < timedelta(seconds=1)


class TestAuthCookieService:
    @pytest.mark.usefixtures("with_valid_cookie")
    def test_verify_cookie(self, service, auth_ticket):
        assert service.verify_cookie() == auth_ticket.user
        # We also set the cache as a side effect

        assert service._user == auth_ticket.user  # pylint: disable=protected-access

    def test_verify_cookie_short_circuits_if_user_cache_is_set(self, service):
        # pylint: disable=protected-access
        service._user = sentinel.user

        assert service.verify_cookie() == service._user

    def test_verify_cookie_returns_None_if_there_is_no_cookie(self, service, cookie):
        cookie.get_value.return_value = None

        assert service.verify_cookie() is None

    def test_verify_cookie_returns_None_if_there_is_no_ticket(self, service, cookie):
        cookie.get_value.return_value = "userid", "MISSING"

        assert service.verify_cookie() is None

    @pytest.mark.usefixtures("with_valid_cookie")
    def test_verify_cookie_returns_None_if_the_ticket_has_expired(
        self, service, auth_ticket
    ):
        auth_ticket.expires = datetime.utcnow() - timedelta(hours=1)

        assert service.verify_cookie() is None

    @pytest.mark.parametrize(
        "offset,expect_update",
        (
            (timedelta(seconds=0), False),
            (AuthCookieService.TICKET_REFRESH_INTERVAL + timedelta(seconds=-1), False),
            (AuthCookieService.TICKET_REFRESH_INTERVAL, True),
            (AuthCookieService.TICKET_REFRESH_INTERVAL + timedelta(seconds=1), True),
        ),
    )
    @pytest.mark.usefixtures("with_valid_cookie")
    def test_verify_cookie_updates_the_expiry_time(
        self, service, auth_ticket, offset, expect_update
    ):
        auth_ticket.updated = datetime.utcnow() - offset
        expires = auth_ticket.expires

        service.verify_cookie()

        if expect_update:
            assert_nearly_equal(
                auth_ticket.expires, datetime.utcnow() + AuthCookieService.TICKET_TTL
            )
        else:
            assert auth_ticket.expires == expires

    def test_create_cookie(self, service, user, user_service, cookie, db_session):
        user_service.fetch.return_value = user

        headers = service.create_cookie(sentinel.userid)

        user_service.fetch.assert_called_once_with(sentinel.userid)

        auth_ticket = db_session.query(AuthTicket).first()
        assert auth_ticket.user == user
        assert auth_ticket.user_userid == user.userid
        assert auth_ticket.id == Any.string.matching(".{30,40}")
        assert_nearly_equal(
            auth_ticket.expires, datetime.utcnow() + AuthCookieService.TICKET_TTL
        )

        cookie.get_headers.assert_called_once_with([user.userid, auth_ticket.id])
        assert headers == cookie.get_headers.return_value
        assert service._user == user  # pylint: disable=protected-access

    def test_create_cookie_raises_if_user_is_missing(self, service, user_service):
        user_service.fetch.return_value = None

        with pytest.raises(ValueError):
            service.create_cookie(sentinel.userid)

    @pytest.mark.usefixtures("with_valid_cookie")
    def test_revoke_cookie(self, service, cookie, db_session):
        headers = service.revoke_cookie()

        cookie.get_headers.assert_called_once_with(None, max_age=0)
        assert headers == cookie.get_headers.return_value
        assert service._user is None  # pylint: disable=protected-access
        assert db_session.query(AuthTicket).first() is None

    def test_revoke_cookie_is_ok_without_a_cookie(self, service):
        service.revoke_cookie()

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def auth_ticket(self, factories):
        return factories.AuthTicket()

    @pytest.fixture
    def cookie(self):
        cookie = create_autospec(SignedCookieProfile, instance=True, spec_set=True)
        cookie.get_value.return_value = None
        return cookie

    @pytest.fixture
    def with_valid_cookie(self, cookie, auth_ticket):
        cookie.get_value.return_value = auth_ticket.user_userid, auth_ticket.id

    @pytest.fixture
    def service(self, db_session, user_service, cookie):
        return AuthCookieService(
            session=db_session, user_service=user_service, cookie=cookie
        )


class TestFactory:
    def test_it(
        self, pyramid_request, SignedCookieProfile, AuthCookieService, user_service
    ):
        pyramid_request.registry.settings[
            "h_auth_cookie_secret"
        ] = sentinel.cookie_secret

        cookie_service = factory(sentinel.context, pyramid_request)

        SignedCookieProfile.assert_called_once_with(
            secret=pyramid_request.registry.settings["h_auth_cookie_secret"],
            salt="authsanity",
            cookie_name="auth",
            secure=True,
            max_age=2592000,
            httponly=True,
        )
        SignedCookieProfile.return_value.bind.assert_called_once_with(pyramid_request)
        AuthCookieService.assert_called_once_with(
            pyramid_request.db,
            user_service=user_service,
            cookie=SignedCookieProfile.return_value.bind.return_value,
        )
        assert cookie_service == AuthCookieService.return_value

    @pytest.fixture
    def SignedCookieProfile(self, patch):
        return patch("h.services.auth_cookie.SignedCookieProfile")

    @pytest.fixture
    def AuthCookieService(self, patch):
        return patch("h.services.auth_cookie.AuthCookieService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.scheme = "https"  # Simulate production environment
        return pyramid_request
