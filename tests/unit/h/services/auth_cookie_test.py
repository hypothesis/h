from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest

from h.models import AuthTicket
from h.services.auth_cookie import AuthCookieService, factory


def assert_nearly_equal(first_date, second_date):
    diff = abs(first_date - second_date)

    assert diff < timedelta(seconds=1)


class TestAuthCookieService:
    def test_verify_ticket(self, service, auth_ticket):
        assert (
            service.verify_ticket(auth_ticket.user.userid, auth_ticket.id)
            == auth_ticket.user
        )
        # We also set the cache as a side effect

        assert service._user == auth_ticket.user  # pylint: disable=protected-access

    def test_verify_ticket_short_circuits_if_user_cache_is_set(self, service):
        # pylint: disable=protected-access
        service._user = sentinel.user

        assert (
            service.verify_ticket(sentinel.userid, sentinel.ticket_id) == service._user
        )

    def test_verify_ticket_returns_None_if_there_is_no_ticket(self, service, user):
        assert service.verify_ticket(user.userid, ticket_id="does_not_exist") is None

    def test_verify_ticket_returns_None_if_the_ticket_has_expired(
        self, service, auth_ticket
    ):
        auth_ticket.expires = datetime.utcnow() - timedelta(hours=1)

        assert service.verify_ticket(auth_ticket.user.userid, auth_ticket.id) is None

    @pytest.mark.parametrize(
        "offset,expect_update",
        (
            (timedelta(seconds=0), False),
            (AuthCookieService.TICKET_REFRESH_INTERVAL + timedelta(seconds=-1), False),
            (AuthCookieService.TICKET_REFRESH_INTERVAL, True),
            (AuthCookieService.TICKET_REFRESH_INTERVAL + timedelta(seconds=1), True),
        ),
    )
    def test_verify_ticket_updates_the_expiry_time(
        self, service, auth_ticket, offset, expect_update
    ):
        auth_ticket.updated = datetime.utcnow() - offset
        expires = auth_ticket.expires

        service.verify_ticket(auth_ticket.user.userid, auth_ticket.id)

        if expect_update:
            assert_nearly_equal(
                auth_ticket.expires, datetime.utcnow() + AuthCookieService.TICKET_TTL
            )
        else:
            assert auth_ticket.expires == expires

    def test_add_ticket(self, service, user, user_service, db_session):
        user_service.fetch.return_value = user

        service.add_ticket(sentinel.userid, "test_ticket_id")

        user_service.fetch.assert_called_once_with(sentinel.userid)
        auth_ticket = db_session.query(AuthTicket).one()
        assert auth_ticket.user == user
        assert auth_ticket.user_userid == user.userid
        assert auth_ticket.id == "test_ticket_id"
        assert_nearly_equal(
            auth_ticket.expires, datetime.utcnow() + AuthCookieService.TICKET_TTL
        )
        assert service._user == user  # pylint: disable=protected-access

    def test_add_ticket_raises_if_user_is_missing(self, service, user_service):
        user_service.fetch.return_value = None

        with pytest.raises(
            ValueError, match=f"Cannot find user with userid {sentinel.userid}"
        ):
            service.add_ticket(sentinel.userid, sentinel.ticket_id)

    def test_remove_ticket(self, auth_ticket, service, db_session):
        service.remove_ticket(auth_ticket.id)

        assert service._user is None  # pylint: disable=protected-access
        assert db_session.query(AuthTicket).first() is None

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def auth_ticket(self, factories):
        return factories.AuthTicket()

    @pytest.fixture
    def service(self, db_session, user_service):
        return AuthCookieService(session=db_session, user_service=user_service)


class TestFactory:
    def test_it(self, pyramid_request, AuthCookieService, user_service):
        cookie_service = factory(sentinel.context, pyramid_request)

        AuthCookieService.assert_called_once_with(
            pyramid_request.db, user_service=user_service
        )
        assert cookie_service == AuthCookieService.return_value

    @pytest.fixture
    def AuthCookieService(self, patch):
        return patch("h.services.auth_cookie.AuthCookieService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.scheme = "https"  # Simulate production environment
        return pyramid_request
