from unittest.mock import sentinel

import pytest

from h.services.search_index.service_factory import factory


class TestFactory:
    def test_it(self, pyramid_request, SearchIndexService, settings):
        result = factory(sentinel.context, pyramid_request)

        SearchIndexService.assert_called_once_with(
            request=pyramid_request,
            es_client=pyramid_request.es,
            session=pyramid_request.db,
            settings=settings,
        )
        assert result == SearchIndexService.return_value

    @pytest.fixture
    def settings(self, pyramid_config):
        settings = sentinel.settings
        pyramid_config.register_service(settings, name="settings")
        return settings

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.es = sentinel.es
        return pyramid_request


@pytest.fixture(autouse=True)
def SearchIndexService(patch):
    return patch("h.services.search_index.service_factory.SearchIndexService")
