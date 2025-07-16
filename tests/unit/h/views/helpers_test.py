from datetime import UTC, datetime
from unittest.mock import create_autospec, sentinel

import pytest

from h.accounts.events import LoginEvent
from h.views import helpers
from h.views.helpers import login


class TestLogin:
    @pytest.mark.usefixtures("frozen_time")
    def test_login(
        self,
        factories,
        login_event_subscriber,
        mocker,
        pyramid_config,
        pyramid_request,
    ):
        pyramid_config.testing_securitypolicy(remember_result=sentinel.headers)
        mocker.spy(helpers, "remember")
        user = factories.User(last_login_date=datetime(1970, 1, 1, tzinfo=UTC))

        headers = login(user, pyramid_request)

        assert user.last_login_date == datetime.now(UTC)
        login_event_subscriber.assert_called_once_with(
            self.LoginEventMatcher(pyramid_request, user)
        )
        helpers.remember.assert_called_once_with(pyramid_request, user.userid)
        assert headers == sentinel.headers

    class LoginEventMatcher:
        def __init__(self, request, user):
            self.request = request
            self.user = user

        def __eq__(self, other):
            return all(
                [
                    isinstance(other, LoginEvent),
                    other.request == self.request,
                    other.user == self.user,
                ]
            )

    @pytest.fixture
    def login_event_subscriber(self, pyramid_config):
        def spec(event):
            """Mock specification for login_event_subscriber below."""

        login_event_subscriber = create_autospec(spec)

        pyramid_config.add_subscriber(login_event_subscriber, LoginEvent)

        return login_event_subscriber
