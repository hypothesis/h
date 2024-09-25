from datetime import datetime, timedelta
from unittest.mock import sentinel

import pytest
from sqlalchemy import inspect

from h.models import AuthTicket
from h.services.auth_ticket import AuthTicketService, factory


def assert_nearly_equal(first_date, second_date):
    diff = abs(first_date - second_date)

    assert diff < timedelta(seconds=1)


class TestAuthTicketService:
    def test_verify_ticket(self, service, auth_ticket):
        assert (
            service.verify_ticket(auth_ticket.user.userid, auth_ticket.id)
            == auth_ticket
        )
        # We also set the cache as a side effect.
        assert service._ticket == auth_ticket  # pylint:disable=protected-access

    def test_verify_ticket_short_circuits_if_ticket_cache_is_set(self, service):
        # pylint: disable=protected-access
        service._ticket = sentinel.ticket

        assert (
            service.verify_ticket(sentinel.userid, sentinel.ticket_id)
            == sentinel.ticket
        )

    @pytest.mark.usefixtures("auth_ticket")
    def test_verify_ticket_returns_None_if_theres_no_matching_ticket(
        self, service, user
    ):
        assert service.verify_ticket(user.userid, ticket_id="does_not_exist") is None

    def test_verify_ticket_when_theres_no_userid(self, service, auth_ticket):
        assert service.verify_ticket(None, ticket_id=auth_ticket.id) is None

    @pytest.mark.usefixtures("auth_ticket")
    def test_verify_ticket_when_theres_no_ticket_id(self, service, user):
        assert service.verify_ticket(user.userid, ticket_id=None) is None

    def test_verify_ticket_returns_None_if_the_ticket_has_expired(
        self, service, auth_ticket
    ):
        auth_ticket.expires = datetime.utcnow() - timedelta(hours=1)

        assert service.verify_ticket(auth_ticket.user.userid, auth_ticket.id) is None

    @pytest.mark.parametrize(
        "offset,expect_update",
        (
            (timedelta(seconds=0), False),
            (AuthTicketService.TICKET_REFRESH_INTERVAL + timedelta(seconds=-1), False),
            (AuthTicketService.TICKET_REFRESH_INTERVAL, True),
            (AuthTicketService.TICKET_REFRESH_INTERVAL + timedelta(seconds=1), True),
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
                auth_ticket.expires, datetime.utcnow() + AuthTicketService.TICKET_TTL
            )
        else:
            assert auth_ticket.expires == expires

    def test_add_ticket(self, service, user, user_service):
        user_service.fetch.return_value = user

        auth_ticket = service.add_ticket(sentinel.userid, "test_ticket_id")

        user_service.fetch.assert_called_once_with(sentinel.userid)
        assert auth_ticket.user == user
        assert auth_ticket.user_userid == user.userid
        assert auth_ticket.id == "test_ticket_id"
        assert_nearly_equal(
            auth_ticket.expires, datetime.utcnow() + AuthTicketService.TICKET_TTL
        )
        assert service._ticket == auth_ticket  # pylint: disable=protected-access
        assert inspect(auth_ticket).pending is True

    def test_add_ticket_raises_if_user_is_missing(self, service, user_service):
        user_service.fetch.return_value = None

        with pytest.raises(
            ValueError, match=f"Cannot find user with userid {sentinel.userid}"
        ):
            service.add_ticket(sentinel.userid, sentinel.ticket_id)

    def test_remove_ticket(self, auth_ticket, service, db_session):
        service.remove_ticket(auth_ticket.id)

        assert service._ticket is None  # pylint: disable=protected-access
        assert db_session.query(AuthTicket).first() is None

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def auth_ticket(self, factories):
        return factories.AuthTicket()

    @pytest.fixture
    def service(self, db_session, user_service):
        return AuthTicketService(session=db_session, user_service=user_service)


class TestFactory:
    def test_it(self, pyramid_request, AuthTicketService, user_service):
        cookie_service = factory(sentinel.context, pyramid_request)

        AuthTicketService.assert_called_once_with(
            pyramid_request.db, user_service=user_service
        )
        assert cookie_service == AuthTicketService.return_value

    @pytest.fixture
    def AuthTicketService(self, patch):
        return patch("h.services.auth_ticket.AuthTicketService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.scheme = "https"  # Simulate production environment
        return pyramid_request
