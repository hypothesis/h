from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from h.models import UserIdentity
from h.models.user_identity import IdentityProvider
from h.services.oidc import MissingSubError, OIDCClient, OIDCClientSettings, factory


class TestOIDCClient:
    def test_get_provider_unique_id(
        self, client, http_service, jwt_service, OIDCTokenResponseSchema
    ):
        jwt_service.decode_oidc_idtoken.return_value = {
            "sub": sentinel.provider_unique_id
        }
        OIDCTokenResponseSchema.return_value.validate.return_value = {
            "id_token": sentinel.id_token
        }

        provider_unique_id = client.get_provider_unique_id(
            IdentityProvider.ORCID, sentinel.authorization_code
        )

        http_service.post.assert_called_once_with(
            sentinel.orcid_token_url,
            data={
                "redirect_uri": sentinel.orcid_redirect_uri,
                "grant_type": "authorization_code",
                "code": sentinel.authorization_code,
            },
            auth=(sentinel.orcid_client_id, sentinel.orcid_client_secret),
        )
        OIDCTokenResponseSchema.return_value.validate.assert_called_once_with(
            http_service.post.return_value.json.return_value
        )
        jwt_service.decode_oidc_idtoken.assert_called_once_with(
            sentinel.id_token, sentinel.orcid_keyset_url, ["RS256"]
        )
        assert provider_unique_id == sentinel.provider_unique_id

    def test_get_provider_unique_id_missing_sub(self, client, jwt_service):
        jwt_service.decode_oidc_idtoken.return_value = {}

        with pytest.raises(MissingSubError):
            client.get_provider_unique_id(
                IdentityProvider.ORCID, sentinel.authorization_code
            )

    def test_add_identity(self, client, db_session, user, matchers):
        client.add_identity(user, IdentityProvider.ORCID, "test_provider_unique_id")

        assert list(db_session.execute(select(UserIdentity)).scalars()) == [
            matchers.InstanceOf(
                UserIdentity,
                provider=IdentityProvider.ORCID,
                provider_unique_id="test_provider_unique_id",
                user_id=user.id,
            )
        ]

    def test_get_identity(self, client, db_session, user):
        identity = UserIdentity(
            user=user,
            provider=IdentityProvider.ORCID,
            provider_unique_id="test_provider_unique_id",
        )
        db_session.add(identity)
        db_session.flush()

        result = client.get_identity(user, IdentityProvider.ORCID)

        assert result == identity

    def test_get_identity_when_no_matching_identity(self, client, user):
        result = client.get_identity(user, IdentityProvider.ORCID)

        assert result is None

    @pytest.fixture
    def client(self, db_session, http_service, user_service, jwt_service):
        return OIDCClient(
            db_session,
            settings={
                IdentityProvider.ORCID: OIDCClientSettings(
                    client_id=sentinel.orcid_client_id,
                    client_secret=sentinel.orcid_client_secret,
                    redirect_uri=sentinel.orcid_redirect_uri,
                    token_url=sentinel.orcid_token_url,
                    keyset_url=sentinel.orcid_keyset_url,
                )
            },
            http_service=http_service,
            user_service=user_service,
            jwt_service=jwt_service,
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()


class TestFactory:
    def test_it(
        self,
        db_session,
        pyramid_request,
        OIDCClient,
        http_service,
        user_service,
        jwt_service,
    ):
        settings = pyramid_request.registry.settings
        settings["oidc_clientid_orcid"] = sentinel.orcid_client_id
        settings["oidc_clientsecret_orcid"] = sentinel.orcid_client_secret
        settings["oidc_tokenurl_orcid"] = sentinel.orcid_token_url
        settings["oidc_keyseturl_orcid"] = sentinel.orcid_keyset_url

        result = factory(sentinel.context, pyramid_request)

        OIDCClient.assert_called_once_with(
            db=db_session,
            settings={
                IdentityProvider.ORCID: OIDCClientSettings(
                    client_id=sentinel.orcid_client_id,
                    client_secret=sentinel.orcid_client_secret,
                    redirect_uri=pyramid_request.route_url("oidc.redirect.orcid"),
                    token_url=sentinel.orcid_token_url,
                    keyset_url=sentinel.orcid_keyset_url,
                )
            },
            http_service=http_service,
            user_service=user_service,
            jwt_service=jwt_service,
        )
        assert result == OIDCClient.return_value

    @pytest.fixture(autouse=True)
    def OIDCClient(self, patch):
        return patch("h.services.oidc.OIDCClient")

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("oidc.redirect.orcid", "/oidc/redirect/orcid")


@pytest.fixture(autouse=True)
def OIDCTokenResponseSchema(patch):
    return patch("h.services.oidc.OIDCTokenResponseSchema")
