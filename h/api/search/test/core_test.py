import mock
import pytest

from h.api.search import core


search_fixtures = pytest.mark.usefixtures('query', 'models')


@search_fixtures
def test_search_passes_private_to_AuthFilter(query):
    request = mock.Mock()

    core.search(request, mock.Mock(), private=True)

    query.AuthFilter.assert_called_once_with(request, True)


@pytest.fixture
def query(request):
    patcher = mock.patch('h.api.search.core.query', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def models(request):
    patcher = mock.patch('h.api.search.core.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
