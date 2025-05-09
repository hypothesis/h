from unittest.mock import sentinel

import pytest

from h.services.exceptions import ExternalRequestError
from h.services.openid_client import OpenIDClientService, factory


class TestOpenIDClientService:
    def test_get_id_token(
        self, svc, http_service, passed_args, RetrieveOpenIDTokenSchema, id_token_data
    ):
        http_response = http_service.post.return_value
        http_response.json.return_value = id_token_data
        RetrieveOpenIDTokenSchema.return_value.validate.return_value = id_token_data

        result = svc.get_id_token(**passed_args)

        http_service.post.assert_called_once_with(
            passed_args["token_url"],
            data={
                "redirect_uri": passed_args["redirect_uri"],
                "grant_type": "authorization_code",
                "code": passed_args["authorization_code"],
            },
            auth=passed_args["auth"],
        )
        RetrieveOpenIDTokenSchema.return_value.validate.assert_called_once_with(
            http_response.json.return_value
        )
        assert result == id_token_data["id_token"]

    def test_get_id_token_raises_if_the_request_fails(
        self, svc, http_service, passed_args
    ):
        http_service.post.side_effect = ExternalRequestError(
            request=sentinel.err_request, response=sentinel.err_response
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.get_id_token(**passed_args)

        assert exc_info.value.request == sentinel.err_request
        assert exc_info.value.response == sentinel.err_response

    @pytest.fixture
    def id_token_data(self):
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "id_token": "test_id_token",
        }

    @pytest.fixture
    def passed_args(self):
        return {
            "token_url": sentinel.token_url,
            "redirect_uri": sentinel.redirect_uri,
            "auth": sentinel.auth,
            "authorization_code": sentinel.authorization_code,
        }

    @pytest.fixture
    def svc(self, http_service):
        return OpenIDClientService(http_service)

    @pytest.fixture(autouse=True)
    def RetrieveOpenIDTokenSchema(self, patch):
        return patch("h.services.openid_client.RetrieveOpenIDTokenSchema")


class TestFactory:
    def test_it(self, pyramid_request, http_service, OpenIDClientService):
        svc = factory(sentinel.context, pyramid_request)

        OpenIDClientService.assert_called_once_with(http_service)
        assert svc == OpenIDClientService.return_value

    @pytest.fixture(autouse=True)
    def OpenIDClientService(self, patch):
        return patch("h.services.openid_client.OpenIDClientService")
