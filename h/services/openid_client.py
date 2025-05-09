import logging
from typing import Any

from h.schemas.oauth import OpenIDTokenData, RetrieveOpenIDTokenSchema
from h.services.http import ExternalRequestError, HTTPService

logger = logging.getLogger(__name__)


class OpenIDTokenError(ExternalRequestError):
    """
    A problem with an Open ID token for an external API.

    This is raised when we don't have an access token for the current user or
    when our access token doesn't work (e.g. because it's expired or been
    revoked).
    """


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
    ) -> OpenIDTokenData:
        response = self._http_service.post(token_url, data=data, auth=auth)

        return RetrieveOpenIDTokenSchema().validate(response.json())


def factory(_context, request) -> OpenIDClientService:
    return OpenIDClientService(request.find_service(HTTPService))
