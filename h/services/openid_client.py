import logging
from typing import Any

from h.schemas.oidc import OIDCTokenResponseSchema
from h.services.http import HTTPService

logger = logging.getLogger(__name__)


class OpenIDClientService:
    def __init__(self, http_service: HTTPService) -> None:
        self._http_service = http_service

    def get_id_token(
        self,
        token_url: str,
        redirect_uri: str,
        auth: tuple[str, str],
        authorization_code: str,
    ) -> str:
        data = self._request_openid_data(
            token_url=token_url,
            auth=auth,
            data={
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": authorization_code,
            },
        )
        return data["id_token"]

    def _request_openid_data(
        self, token_url: str, data: dict[str, Any], auth: tuple[str, str]
    ) -> OIDCTokenResponseSchema.OIDCTokenResponseData:
        response = self._http_service.post(token_url, data=data, auth=auth)

        return OIDCTokenResponseSchema().validate(response.json())


def factory(_context, request) -> OpenIDClientService:
    return OpenIDClientService(request.find_service(HTTPService))
