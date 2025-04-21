import logging

from h.services.jwt import JWTService
from h.services.oauth2_client import OAuth2ClientService

logger = logging.getLogger(__name__)


class ORCIDClientService:
    def __init__(
        self,
        host: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        oauth_client_service: OAuth2ClientService,
        jwt_service: JWTService,
    ) -> None:
        self._host = host
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._oauth_client_service = oauth_client_service
        self._jwt_service = jwt_service

    def _get_id_token(self, authorization_code: str) -> str:
        return self._oauth_client_service.get_id_token(
            token_url=self.token_url,
            redirect_uri=self._redirect_uri,
            auth=(self._client_id, self._client_secret),
            authorization_code=authorization_code,
        )

    def get_orcid(self, authorization_code: str) -> str:
        id_token = self._get_id_token(authorization_code)
        decoded_id_token = self._jwt_service.decode_id_token(id_token, self.key_set_url)
        logger.debug("decoded_id_token: %s", decoded_id_token)
        return decoded_id_token["sub"]

    @property
    def token_url(self) -> str:
        return self._api_url("oauth/token")

    @property
    def key_set_url(self) -> str:
        return self._api_url("oauth/jwks")

    def _api_url(self, path: str) -> str:
        return f"https://{self._host}/{path}"


def factory(_context, request) -> ORCIDClientService:
    settings = request.registry.settings

    return ORCIDClientService(
        host=settings["orcid_host"],
        client_id=settings["orcid_client_id"],
        client_secret=settings["orcid_client_secret"],
        redirect_uri=request.route_url("orcid.oauth.callback"),
        oauth_client_service=request.find_service(OAuth2ClientService),
        jwt_service=request.find_service(JWTService),
    )
