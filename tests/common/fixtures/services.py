from unittest import mock

import pytest

from h.services.nipsa import NipsaService


@pytest.fixture
def nipsa_service(pyramid_config):
    service = mock.create_autospec(NipsaService, spec_set=True, instance=True)
    service.is_flagged.return_value = False

    pyramid_config.register_service(service, name="nipsa")
    return service
