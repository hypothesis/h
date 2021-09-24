from unittest import mock

import pytest
from oauthlib.common import Request as OAuthRequest

from h.services.oauth._bearer_token import BearerToken


class TestBearerToken:
    @pytest.mark.parametrize(
        "attr",
        [
            "request_validator",
            "token_generator",
            "expires_in",
            "refresh_token_generator",
            "refresh_token_expires_in",
        ],
    )
    def test_init_sets_instance_vars(self, attr):
        value = mock.Mock()
        token = BearerToken(**{attr: value})
        assert getattr(token, attr) == value

    def test_create_token_sets_refresh_token_expires_in(self, oauth_request):
        value = mock.Mock()
        token = BearerToken(
            request_validator=mock.Mock(), refresh_token_expires_in=value
        )

        assert oauth_request.extra_credentials is None
        token.create_token(oauth_request)
        assert oauth_request.extra_credentials.get("refresh_token_expires_in") == value

    def test_create_token_does_not_override_extras(self, oauth_request):
        value = mock.Mock()
        token = BearerToken(
            request_validator=mock.Mock(), refresh_token_expires_in=value
        )

        oauth_request.extra_credentials = {"foo": "bar"}
        token.create_token(oauth_request)
        assert oauth_request.extra_credentials.get("refresh_token_expires_in") == value
        assert oauth_request.extra_credentials.get("foo") == "bar"

    @pytest.fixture
    def oauth_request(self):
        return OAuthRequest("/")
