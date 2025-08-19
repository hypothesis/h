from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from h.models import UserIdentity
from h.models.user_identity import IdentityProvider
from h.services.oidc import MissingSubError, OIDCService, OIDCServiceSettings, factory


class TestOIDCService:
    def test_get_decoded_idtoken(
        self, client, http_service, jwt_service, OIDCTokenResponseSchema
    ):
        jwt_service.decode_oidc_idtoken.return_value = {
            "sub": sentinel.provider_unique_id
        }
        OIDCTokenResponseSchema.return_value.validate.return_value = {
            "id_token": sentinel.id_token
        }

        decoded_idtoken = client.get_decoded_idtoken(
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
            sentinel.id_token, sentinel.orcid_keyset_url
        )
        assert decoded_idtoken == jwt_service.decode_oidc_idtoken.return_value

    def test_get_decoded_idtoken_missing_sub(self, client, jwt_service):
        jwt_service.decode_oidc_idtoken.return_value = {}

        with pytest.raises(MissingSubError):
            client.get_decoded_idtoken(
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
        return OIDCService(
            db_session,
            settings={
                IdentityProvider.ORCID: OIDCServiceSettings(
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
        OIDCService,
        http_service,
        user_service,
        jwt_service,
    ):
        settings = pyramid_request.registry.settings
        settings["oidc_clientid_orcid"] = sentinel.orcid_client_id
        settings["oidc_clientid_google"] = sentinel.google_client_id
        settings["oidc_clientid_facebook"] = sentinel.facebook_client_id
        settings["oidc_clientsecret_orcid"] = sentinel.orcid_client_secret
        settings["oidc_clientsecret_google"] = sentinel.google_client_secret
        settings["oidc_clientsecret_facebook"] = sentinel.facebook_client_secret
        settings["oidc_tokenurl_orcid"] = sentinel.orcid_token_url
        settings["oidc_tokenurl_google"] = sentinel.google_token_url
        settings["oidc_tokenurl_facebook"] = sentinel.facebook_token_url
        settings["oidc_keyseturl_orcid"] = sentinel.orcid_keyset_url
        settings["oidc_keyseturl_google"] = sentinel.google_keyset_url
        settings["oidc_keyseturl_facebook"] = sentinel.facebook_keyset_url

        result = factory(sentinel.context, pyramid_request)

        OIDCService.assert_called_once_with(
            db=db_session,
            settings={
                IdentityProvider.ORCID: OIDCServiceSettings(
                    client_id=sentinel.orcid_client_id,
                    client_secret=sentinel.orcid_client_secret,
                    redirect_uri=pyramid_request.route_url("oidc.redirect.orcid"),
                    token_url=sentinel.orcid_token_url,
                    keyset_url=sentinel.orcid_keyset_url,
                ),
                IdentityProvider.GOOGLE: OIDCServiceSettings(
                    client_id=sentinel.google_client_id,
                    client_secret=sentinel.google_client_secret,
                    redirect_uri=pyramid_request.route_url("oidc.redirect.google"),
                    token_url=sentinel.google_token_url,
                    keyset_url=sentinel.google_keyset_url,
                ),
                IdentityProvider.FACEBOOK: OIDCServiceSettings(
                    client_id=sentinel.facebook_client_id,
                    client_secret=sentinel.facebook_client_secret,
                    redirect_uri=pyramid_request.route_url("oidc.redirect.facebook"),
                    token_url=sentinel.facebook_token_url,
                    keyset_url=sentinel.facebook_keyset_url,
                ),
            },
            http_service=http_service,
            user_service=user_service,
            jwt_service=jwt_service,
        )
        assert result == OIDCService.return_value

    @pytest.fixture(autouse=True)
    def OIDCService(self, patch):
        return patch("h.services.oidc.OIDCService")

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("oidc.redirect.orcid", "/oidc/redirect/orcid")
        pyramid_config.add_route("oidc.redirect.google", "/oidc/redirect/google")
        pyramid_config.add_route("oidc.redirect.facebook", "/oidc/redirect/facebook")


@pytest.fixture(autouse=True)
def OIDCTokenResponseSchema(patch):
    return patch("h.services.oidc.OIDCTokenResponseSchema")
