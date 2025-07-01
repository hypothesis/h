from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from h.models import UserIdentity
from h.models.user_identity import IdentityProvider
from h.services.orcid_client import ORCIDClientService, factory


class TestORCIDClientService:
    def test_get_orcid(self, service, openid_client_service, JWTService):
        openid_client_service.get_id_token.return_value = sentinel.id_token
        JWTService.decode_token.return_value = {"sub": sentinel.orcid}

        orcid = service.get_orcid(sentinel.authorization_code)

        assert orcid == sentinel.orcid
        openid_client_service.get_id_token.assert_called_once_with(
            token_url=service.token_url,
            redirect_uri=sentinel.redirect_uri,
            auth=(sentinel.client_id, sentinel.client_secret),
            authorization_code=sentinel.authorization_code,
        )
        JWTService.decode_token.assert_called_once_with(
            sentinel.id_token, service.key_set_url, ["RS256"]
        )

    def test_get_orcid_returns_none_if_sub_missing(
        self, service, openid_client_service, JWTService
    ):
        openid_client_service.get_id_token.return_value = sentinel.id_token
        JWTService.decode_token.return_value = {}

        assert service.get_orcid(sentinel.authorization_code) is None

    def test_add_identity(self, service, db_session, user):
        orcid = "1111-1111-1111-1111"

        service.add_identity(user, orcid)

        stmt = select(UserIdentity).where(
            UserIdentity.user == user,
            UserIdentity.provider == IdentityProvider.ORCID,
            UserIdentity.provider_unique_id == orcid,
        )
        assert db_session.execute(stmt).scalar() is not None

    def test_get_identity(self, service, user, user_identity):
        assert service.get_identity(user) == user_identity

    def test_get_identity_without_identities(self, service, user):
        user.identities = []

        assert service.get_identity(user) is None

    def test_orcid_url_with_empty_orcid(self, service):
        assert service.orcid_url("") is None

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def user_identity(self, user, db_session):
        identity = UserIdentity(
            user=user,
            provider=IdentityProvider.ORCID,
            provider_unique_id="0000-0000-0000-0000",
        )
        db_session.add(identity)
        db_session.flush()
        return identity

    @pytest.fixture
    def service(self, db_session, openid_client_service, user_service):
        return ORCIDClientService(
            db=db_session,
            host=IdentityProvider.ORCID,
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
            openid_client_service=openid_client_service,
            user_service=user_service,
        )

    @pytest.fixture(autouse=True)
    def JWTService(self, patch):
        return patch("h.services.orcid_client.JWTService")


class TestFactory:
    def test_it(
        self, pyramid_request, ORCIDClientService, openid_client_service, user_service
    ):
        service = factory(sentinel.context, pyramid_request)

        ORCIDClientService.assert_called_once_with(
            db=pyramid_request.db,
            host=IdentityProvider.ORCID,
            client_id=sentinel.client_id,
            client_secret=sentinel.client_secret,
            redirect_uri=sentinel.redirect_uri,
            openid_client_service=openid_client_service,
            user_service=user_service,
        )
        assert service == ORCIDClientService.return_value

    @pytest.fixture(autouse=True)
    def ORCIDClientService(self, patch):
        return patch("h.services.orcid_client.ORCIDClientService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request, mocker):
        pyramid_request.registry.settings.update(
            {
                "orcid_host": IdentityProvider.ORCID,
                "orcid_client_id": sentinel.client_id,
                "orcid_client_secret": sentinel.client_secret,
            }
        )
        pyramid_request.route_url = mocker.Mock(return_value=sentinel.redirect_uri)
        return pyramid_request
