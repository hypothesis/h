from h.auth.util import client_authority, default_authority
from h.security import Identity


class TestClientAuthority:
    def test_it_with_no_identity(self, pyramid_request, pyramid_config):
        self.set_identity(pyramid_request, pyramid_config, identity=None)

        result = client_authority(pyramid_request)

        assert result is None

    def test_it_with_auth_client(self, pyramid_request, pyramid_config, factories):
        identity = Identity(auth_client=factories.AuthClient())
        self.set_identity(pyramid_request, pyramid_config, identity=identity)

        result = client_authority(pyramid_request)

        assert result == identity.auth_client.authority

    def set_identity(self, pyramid_request, pyramid_config, identity):
        try:
            # Pyramid 2.0
            pyramid_config.testing_securitypolicy(identity=identity)
        except TypeError:
            # Pyramid 1.x
            pyramid_request.identity = identity


class TestAuthDomain:
    def test_it_returns_the_request_domain_if_authority_isnt_set(self, pyramid_request):
        # Make sure h.authority isn't set.
        pyramid_request.registry.settings.pop("h.authority", None)

        assert default_authority(pyramid_request) == pyramid_request.domain

    def test_it_allows_overriding_request_domain(self, pyramid_request):
        pyramid_request.registry.settings["h.authority"] = "foo.org"
        assert default_authority(pyramid_request) == "foo.org"

    def test_it_returns_str(self, pyramid_request):
        pyramid_request.domain = str(pyramid_request.domain)
        assert isinstance(default_authority(pyramid_request), str)
