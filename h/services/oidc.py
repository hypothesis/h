from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import select

from h.models import User, UserIdentity
from h.models.user_identity import IdentityProvider
from h.schemas.oidc import OIDCTokenResponseSchema
from h.services.http import HTTPService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from h.services import JWTService, UserService


@dataclass
class OIDCServiceSettings:
    """Per-provider settings for OIDCService."""

    client_id: str
    """Our OAuth/OIDC client_id for this provider."""

    client_secret: str
    """Our OAuth/OIDC client_id for this provider."""

    redirect_uri: str
    """Our OAuth/OIDC redirect_uri for this provider."""

    token_url: str
    """The URL of the provider's OIDC token endpoint.

    This is the endpoint that we make a server-to-server request to in order to
    get the ID token (JWT) that contains the provider's unique ID and other
    information about the user.
    """

    keyset_url: str
    """The provider's JWKS keyset URL.

    This is the URL from which we fetch the provider's public key which we use
    to verify the provider's signature on the ID token.
    """


class MissingSubError(Exception):
    def __init__(self):
        super().__init__("Received an OIDC ID token with no 'sub'.")


class OIDCService:
    def __init__(
        self,
        db: Session,
        settings: dict[IdentityProvider, OIDCServiceSettings],
        http_service: HTTPService,
        user_service: UserService,
        jwt_service: JWTService,
    ) -> None:
        self._db = db
        self._settings = settings
        self._http_service = http_service
        self._user_service = user_service
        self._jwt_service = jwt_service

    def get_provider_unique_id(
        self, provider: IdentityProvider, authorization_code: str
    ) -> str:
        """Return the provider unique ID associated with `authorization_code`.

        This happens during the OIDC authorization flow after the user
        authorizes us to access their account with the provider and the
        provider redirects the browser to us with an authorization_code. This
        method makes a server-to-server request to the provider's authorization
        server to exchange the given authorization_code for provider's unique
        ID for the user.
        """
        settings = self._settings[provider]

        token_response = self._http_service.post(
            settings.token_url,
            data={
                "redirect_uri": settings.redirect_uri,
                "grant_type": "authorization_code",
                "code": authorization_code,
            },
            auth=(settings.client_id, settings.client_secret),
        )

        id_token = OIDCTokenResponseSchema().validate(token_response.json())["id_token"]

        decoded_id_token = self._jwt_service.decode_oidc_idtoken(
            id_token, settings.keyset_url
        )

        try:
            return decoded_id_token["sub"]
        except KeyError as err:
            raise MissingSubError from err

    def add_identity(
        self, user: User, provider: IdentityProvider, provider_unique_id: str
    ) -> None:
        self._db.add(
            UserIdentity(
                user=user, provider=provider, provider_unique_id=provider_unique_id
            )
        )

    def get_identity(
        self, user: User, provider: IdentityProvider
    ) -> UserIdentity | None:
        return self._db.execute(
            select(UserIdentity).where(
                UserIdentity.user_id == user.id,
                UserIdentity.provider == provider,
            )
        ).scalar()


def factory(_context, request) -> OIDCService:
    settings = request.registry.settings

    return OIDCService(
        db=request.db,
        settings={
            IdentityProvider.ORCID: OIDCServiceSettings(
                client_id=settings["oidc_clientid_orcid"],
                client_secret=settings["oidc_clientsecret_orcid"],
                redirect_uri=request.route_url("oidc.redirect.orcid"),
                token_url=settings["oidc_tokenurl_orcid"],
                keyset_url=settings["oidc_keyseturl_orcid"],
            ),
            IdentityProvider.GOOGLE: OIDCServiceSettings(
                client_id=settings["oidc_clientid_google"],
                client_secret=settings["oidc_clientsecret_google"],
                redirect_uri=request.route_url("oidc.redirect.google"),
                token_url=settings["oidc_tokenurl_google"],
                keyset_url=settings["oidc_keyseturl_google"],
            ),
            IdentityProvider.FACEBOOK: OIDCServiceSettings(
                client_id=settings["oidc_clientid_facebook"],
                client_secret=settings["oidc_clientsecret_facebook"],
                redirect_uri=request.route_url("oidc.redirect.facebook"),
                token_url=settings["oidc_tokenurl_facebook"],
                keyset_url=settings["oidc_keyseturl_facebook"],
            ),
        },
        http_service=request.find_service(HTTPService),
        user_service=request.find_service(name="user"),
        jwt_service=request.find_service(name="jwt"),
    )
