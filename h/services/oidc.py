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


# The list of algorithms that we allow authorization servers to use to
# digitally sign and/or encrypt OpenID Connect ID tokens.
#
# The JWT spec leaves it up to the application (us) to specify the list of
# acceptable algorithms when decoding a JWT. You don't (for example) read the
# algorithm from the JWT's `alg` header as this would allow an attacker to
# inject the "None" algorithm or get up to other mischief.
#
# The OpenID Connect spec says that ID tokens SHOULD be signed and/or encrypted
# with RS256.
OIDC_ALLOWED_JWT_ALGORITHMS = ["RS256"]


@dataclass
class OIDCClientSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    token_url: str
    keyset_url: str


class MissingSubError(Exception):
    def __init__(self):
        super().__init__("Received an OIDC ID token with no 'sub'.")


class OIDCClient:
    def __init__(
        self,
        db: Session,
        settings: dict[str, OIDCClientSettings],
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
        token_url = settings.token_url
        redirect_uri = settings.redirect_uri
        client_id = settings.client_id
        client_secret = settings.client_secret
        keyset_url = settings.keyset_url

        token_response = self._http_service.post(
            token_url,
            data={
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": authorization_code,
            },
            auth=(client_id, client_secret),
        )

        id_token = OIDCTokenResponseSchema().validate(token_response.json())["id_token"]

        decoded_id_token = self._jwt_service.decode_oidc_idtoken(
            id_token, keyset_url, OIDC_ALLOWED_JWT_ALGORITHMS
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


def factory(_context, request) -> OIDCClient:
    settings = request.registry.settings

    return OIDCClient(
        db=request.db,
        settings={
            IdentityProvider.ORCID: OIDCClientSettings(
                client_id=settings["oidc_clientid_orcid"],
                client_secret=settings["oidc_clientsecret_orcid"],
                redirect_uri=request.route_url("oidc.redirect.orcid"),
                token_url=settings["oidc_tokenurl_orcid"],
                keyset_url=settings["oidc_keyseturl_orcid"],
            ),
        },
        http_service=request.find_service(HTTPService),
        user_service=request.find_service(name="user"),
        jwt_service=request.find_service(name="jwt"),
    )
