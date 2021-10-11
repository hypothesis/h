from h.auth.util import client_authority
from h.security import Identity


class TestClientAuthority:
    def test_it_with_no_identity(self, pyramid_request, pyramid_config):
        pyramid_config.testing_securitypolicy(identity=None)

        result = client_authority(pyramid_request)

        assert result is None

    def test_it_with_auth_client(self, pyramid_request, pyramid_config, factories):
        identity = Identity.from_models(auth_client=factories.AuthClient())
        pyramid_config.testing_securitypolicy(identity=identity)

        result = client_authority(pyramid_request)

        assert result == identity.auth_client.authority
