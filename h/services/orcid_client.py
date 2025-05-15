import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from h.models import User, UserIdentity
from h.models.user_identity import IdentityProvider
from h.services.jwt import JWTService
from h.services.openid_client import OpenIDClientService
from h.services.user import UserService

logger = logging.getLogger(__name__)


class ORCIDClientService:
    def __init__(  # noqa: PLR0913
        self,
        db: Session,
        host: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        openid_client_service: OpenIDClientService,
        user_service: UserService,
    ) -> None:
        self._db = db
        self._host = host
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._openid_client_service = openid_client_service
        self._user_service = user_service

    def _get_id_token(self, authorization_code: str) -> str:
        return self._openid_client_service.get_id_token(
            token_url=self.token_url,
            redirect_uri=self._redirect_uri,
            auth=(self._client_id, self._client_secret),
            authorization_code=authorization_code,
        )

    def get_orcid(self, authorization_code: str) -> str | None:
        id_token = self._get_id_token(authorization_code)
        decoded_id_token = JWTService.decode_token(id_token, self.key_set_url)
        return decoded_id_token.get("sub")

    def add_identity(self, user: User, orcid: str) -> None:
        identity = UserIdentity(
            user=user,
            provider=IdentityProvider.ORCID,
            provider_unique_id=orcid,
        )
        self._db.add(identity)

    def get_identity(self, user: User) -> UserIdentity | None:
        stmt = select(UserIdentity).where(
            UserIdentity.user_id == user.id,
            UserIdentity.provider == IdentityProvider.ORCID,
        )
        return self._db.execute(stmt).scalar()

    @property
    def token_url(self) -> str:
        return self._api_url("oauth/token")

    @property
    def key_set_url(self) -> str:
        return self._api_url("oauth/jwks")

    def orcid_url(self, orcid: str | None) -> str | None:
        return self._api_url(orcid) if orcid else None

    def _api_url(self, path: str) -> str:
        return f"https://{self._host}/{path}"


def factory(_context, request) -> ORCIDClientService:
    settings = request.registry.settings

    return ORCIDClientService(
        db=request.db,
        host=settings["orcid_host"],
        client_id=settings["orcid_client_id"],
        client_secret=settings["orcid_client_secret"],
        redirect_uri=request.route_url("orcid.oauth.callback"),
        openid_client_service=request.find_service(OpenIDClientService),
        user_service=request.find_service(name="user"),
    )
