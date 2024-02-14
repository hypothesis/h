import pytest
from h_matchers import Any

from h import models
from h.services.developer_token import (
    DeveloperTokenService,
    developer_token_service_factory,
)

pytestmark = pytest.mark.usefixtures("user_service")


class TestDeveloperTokenService:
    def test_fetch_returns_developer_token_for_userid(
        self, svc, developer_token, user, user_service
    ):
        user_service.fetch.return_value = user

        assert svc.fetch(user.userid) == developer_token
        user_service.fetch.assert_called_once_with(user.userid)

    def test_fetch_returns_none_for_missing_userid(self, svc):
        assert svc.fetch(None) is None

    def test_fetch_returns_none_for_missing_developer_token(
        self, svc, user, user_service
    ):
        user_service.fetch.return_value = user

        assert svc.fetch(user.userid) is None
        user_service.fetch.assert_called_once_with(user.userid)

    def test_create_creates_new_developer_token_for_userid(
        self, svc, db_session, user, user_service
    ):
        assert not db_session.query(models.Token).count()
        user_service.fetch.return_value = user

        svc.create(user.userid)

        user_service.fetch.assert_called_once_with(user.userid)
        assert db_session.query(models.Token).all() == [
            Any.instance_of(models.Token).with_attrs({"user": user})
        ]

    def test_create_returns_new_developer_token_for_userid(
        self, svc, user, patch, user_service
    ):
        user_service.fetch.return_value = user
        token_urlsafe = patch("h.services.developer_token.security.token_urlsafe")
        token_urlsafe.return_value = "secure-token"

        token = svc.create(user.userid)

        assert token.user == user
        assert token.value == "6879-secure-token"
        assert token.expires is None
        assert token.authclient is None
        assert token.refresh_token is None

    def test_regenerate_sets_a_new_token_value(self, svc, developer_token):
        old_user = developer_token.user
        old_value = developer_token.value

        svc.regenerate(developer_token)

        assert old_user == developer_token.user
        assert old_value != developer_token.value

    @pytest.fixture
    def svc(self, pyramid_request):
        return developer_token_service_factory(None, pyramid_request)

    @pytest.fixture
    def developer_token(self, factories, user):
        return factories.DeveloperToken(user=user)

    @pytest.fixture
    def user(self, factories):
        return factories.User()


class TestDeveloperTokenServiceFactory:
    def test_it_returns_developer_token_service(self, pyramid_request):
        svc = developer_token_service_factory(None, pyramid_request)
        assert isinstance(svc, DeveloperTokenService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = developer_token_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db
