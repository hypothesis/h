from unittest.mock import create_autospec

import pytest

from h.services.nipsa import NipsaService
from h.services.search_index import SearchIndexService

# Allow people to mass import everything without getting things we don't
# mean them to like pytest.
__all__ = ("service_mocker", "search_index")


@pytest.fixture
def service_mocker(pyramid_config):
    def service_mocker(class_, name):
        service = create_autospec(class_, instance=True)
        pyramid_config.register_service(service, name=name)

        return service

    return service_mocker


@pytest.fixture
def search_index(service_mocker):
    return service_mocker(SearchIndexService, "search_index")


@pytest.fixture
def nipsa_service(pyramid_config):
    return service_mocker(NipsaService, name="nipsa")
