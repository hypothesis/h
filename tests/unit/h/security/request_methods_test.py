import pytest

from h.security import Identity
from h.security.request_methods import default_authority, effective_authority


class TestDefaultAuthority:
    def test_it(self, pyramid_request):
        pyramid_request.registry.settings["h.authority"] = "foo.org"
        assert default_authority(pyramid_request) == "foo.org"

    def test_it_returns_the_request_domain_if_authority_isnt_set(self, pyramid_request):
        pyramid_request.registry.settings.pop("h.authority", None)

        assert default_authority(pyramid_request) == pyramid_request.domain


class TestEffectiveAuthority:
    def test_it_with_auth_client(self, pyramid_request, identity):
        result = effective_authority(pyramid_request)

        assert result == identity.auth_client.authority

    def test_it_returns_default_authority_with_no_auth_client(
        self, pyramid_request, identity
    ):
        identity.auth_client = None

        result = effective_authority(pyramid_request)

        assert result == pyramid_request.default_authority

    def test_it_returns_default_authority_with_no_identity(self, pyramid_request):
        result = effective_authority(pyramid_request)

        assert result == pyramid_request.default_authority

    @pytest.fixture
    def identity(self, pyramid_config, factories):
        identity = Identity.from_models(auth_client=factories.AuthClient())

        pyramid_config.testing_securitypolicy(identity=identity)

        return identity
