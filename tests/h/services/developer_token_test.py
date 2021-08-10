import pytest

from h import models
from h.services.developer_token import (
    DeveloperTokenService,
    developer_token_service_factory,
)


class TestDeveloperTokenService:
    def test_fetch_returns_developer_token_for_userid(
        self, svc, developer_token, userid
    ):
        assert svc.fetch(userid) == developer_token

    def test_fetch_returns_none_for_missing_developer_token(self, svc, userid):
        assert svc.fetch(userid) is None

    def test_create_creates_new_developer_token_for_userid(
        self, svc, db_session, userid
    ):
        assert not db_session.query(models.Token).count()
        svc.create(userid)
        assert db_session.query(models.Token).count() == 1

    def test_create_returns_new_developer_token_for_userid(self, svc, userid, patch):
        token_urlsafe = patch("h.services.developer_token.security.token_urlsafe")
        token_urlsafe.return_value = "secure-token"

        token = svc.create(userid)

        assert token.userid == userid
        assert token.value == "6879-secure-token"
        assert token.expires is None
        assert token.authclient is None
        assert token.refresh_token is None

    def test_regenerate_sets_a_new_token_value(self, svc, developer_token):
        old_userid = developer_token.userid
        old_value = developer_token.value

        svc.regenerate(developer_token)

        assert old_userid == developer_token.userid
        assert old_value != developer_token.value

    @pytest.fixture
    def svc(self, pyramid_request):
        return developer_token_service_factory(None, pyramid_request)

    @pytest.fixture
    def developer_token(self, factories, userid):
        return factories.DeveloperToken(userid=userid)

    @pytest.fixture
    def userid(self):
        return "acct:john@doe.org"


class TestDeveloperTokenServiceFactory:
    def test_it_returns_developer_token_service(self, pyramid_request):
        svc = developer_token_service_factory(None, pyramid_request)
        assert isinstance(svc, DeveloperTokenService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = developer_token_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db
