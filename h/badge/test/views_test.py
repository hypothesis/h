import pytest
import mock

from pyramid import httpexceptions

from h.badge import views


blocklist_fixtures = pytest.mark.usefixtures('models', 'search_lib')


@blocklist_fixtures
def test_blocklist_returns_number_from_search_lib(search_lib):
    request = mock.Mock(params={'uri': 'test_uri'})
    search_lib.search.return_value = {'total': 29}

    result = views.blocklist(request)

    search_lib.search.assert_called_once_with(
        request, {'uri': 'test_uri', 'limit': 0})
    assert result['total'] == search_lib.search.return_value['total']


@blocklist_fixtures
def test_blocklist_returns_blocked_from_model(models):
    request = mock.Mock(params={'uri': 'test_uri'})

    result = views.blocklist(request)

    models.Blocklist.is_blocked.assert_called_once_with('test_uri')
    assert result['blocked'] == models.Blocklist.is_blocked.return_value


@blocklist_fixtures
def test_blocklist_raises_if_no_uri():
    with pytest.raises(httpexceptions.HTTPBadRequest):
        views.blocklist(mock.Mock(params={}))


@pytest.fixture
def models(config, request):  # pylint:disable=unused-argument
    patcher = mock.patch('h.badge.views.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def search_lib(config, request):  # pylint:disable=unused-argument
    patcher = mock.patch('h.badge.views.search_lib', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
