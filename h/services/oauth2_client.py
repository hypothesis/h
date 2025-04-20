import logging

from h.services.http import ExternalRequestError, HTTPService

logger = logging.getLogger(__name__)


class OAuth2TokenError(ExternalRequestError):
    """
    A problem with an OAuth 2 token for an external API.

    This is raised when we don't have an access token for the current user or
    when our access token doesn't work (e.g. because it's expired or been
    revoked).
    """


class OAuth2ClientService:
    def __init__(self, http_service: HTTPService) -> None:
        self._http_service = http_service

    def get_id_token(
        self, token_url: str, redirect_uri: str, auth, authorization_code: str
    ) -> str:
        self._id_token_request(
            token_url=token_url,
            auth=auth,
            data={
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": authorization_code,
            },
        )

    def _id_token_request(self, token_url: str, data, auth) -> str:
        response = self._http_service.post(token_url, data=data, auth=auth)

        data = response.json()

        return data["id_token"]


def factory(_context, request) -> OAuth2ClientService:
    """Return OAuth2HTTPService instance for the passed context and request."""
    return OAuth2ClientService(request.find_service(name="http"))
