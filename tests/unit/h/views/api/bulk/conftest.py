import pytest

from h.security import Identity


@pytest.fixture
def with_auth_client(factories, pyramid_config):
    pyramid_config.testing_securitypolicy(
        identity=Identity.from_models(auth_client=factories.AuthClient())
    )
