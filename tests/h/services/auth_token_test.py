import datetime

import pytest

from h.services.auth_token import AuthTokenService, auth_token_service_factory


class TestAuthTokenService:
    def test_validate_returns_database_token(self, svc, factories):
        token_model = factories.DeveloperToken(expires=self.time(1))

        result = svc.validate(token_model.value)

        assert result.expires == token_model.expires
        assert result.userid == token_model.userid

    def test_validate_caches_database_token(self, svc, factories, db_session):
        token_model = factories.DeveloperToken(expires=self.time(1))

        svc.validate(token_model.value)
        db_session.delete(token_model)
        result = svc.validate(token_model.value)

        assert result is not None

    def test_validate_returns_none_for_cached_invalid_token(
        self, svc, factories, db_session
    ):
        token_model = factories.DeveloperToken(expires=self.time(-1))

        svc.validate(token_model.value)
        db_session.delete(token_model)
        result = svc.validate(token_model.value)

        assert result is None

    def test_validate_returns_none_for_invalid_database_token(self, svc, factories):
        token_model = factories.DeveloperToken(expires=self.time(-1))

        result = svc.validate(token_model.value)

        assert result is None

    def test_validate_returns_none_for_non_existing_token(self, svc):
        result = svc.validate("abcde123")

        assert result is None

    def test_fetch_returns_database_model(self, svc, token):
        assert svc.fetch(token.value) == token

    @pytest.mark.parametrize(
        "header,expected",
        (
            ("Bearer abcdef123", "abcdef123"),
            (None, None),
            ("Bearer ", None),
            ("", None),
            ("abcdef123", None),
            ("\x10", None),
            (".\x00\"Ħ(\x12'𨳂\x05\U000df02a\U00095c2c셀", None),
            ("\U000f022b\t\x07\x1c0\x04\x06", None),
        ),
    )
    def test_get_bearer_token(self, pyramid_request, header, expected):
        if header is not None:
            pyramid_request.headers["Authorization"] = header

        assert AuthTokenService.get_bearer_token(pyramid_request) == expected

    @pytest.mark.usefixtures("token")
    def test_fetch_returns_none_when_not_found(self, svc):
        assert svc.fetch("bogus") is None

    @pytest.fixture
    def svc(self, db_session):
        return AuthTokenService(db_session)

    @pytest.fixture
    def token(self, factories):
        return factories.DeveloperToken()

    def time(self, days_delta=0):
        return datetime.datetime.utcnow() + datetime.timedelta(days=days_delta)


@pytest.mark.usefixtures("pyramid_settings")
class TestAuthTokenServiceFactory:
    def test_it_returns_service(self, pyramid_request):
        result = auth_token_service_factory(None, pyramid_request)

        assert isinstance(result, AuthTokenService)

    def test_it_passes_session(self, pyramid_request, mocked_service):
        auth_token_service_factory(None, pyramid_request)

        mocked_service.assert_called_once_with(pyramid_request.db)

    @pytest.fixture
    def mocked_service(self, patch):
        return patch("h.services.auth_token.AuthTokenService")
