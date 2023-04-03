import colander
import pytest

from h.schemas.auth_client import CreateAuthClientSchema

pytestmark = pytest.mark.usefixtures("pyramid_config")


class TestCreateAuthClientSchema:
    def test_it_allows_valid_authcode_data(self, authcode_data, bound_schema):
        bound_schema.deserialize(authcode_data)

    def test_it_allows_valid_clientcredentials_data(
        self, client_credentials_data, bound_schema
    ):
        bound_schema.deserialize(client_credentials_data)

    def test_it_raises_if_redirect_url_missing(self, authcode_data, bound_schema):
        authcode_data["redirect_url"] = None

        with pytest.raises(
            colander.Invalid, match='Required when grant type is "authorization_code"'
        ):
            bound_schema.deserialize(authcode_data)

    @pytest.fixture
    def authcode_data(self):
        return {
            "name": "Test client",
            "authority": "example.com",
            "grant_type": "authorization_code",
            "trusted": False,
            "redirect_url": "https://test-client.com/oauth-redirect",
        }

    @pytest.fixture
    def client_credentials_data(self):
        return {
            "name": "Test client",
            "authority": "example.com",
            "grant_type": "client_credentials",
        }

    @pytest.fixture
    def bound_schema(self, pyramid_csrf_request):
        return CreateAuthClientSchema().bind(request=pyramid_csrf_request)
