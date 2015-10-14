import pytest
import mock

from pyramid import httpexceptions

from h.blocklist import views


uriinfo_fixtures = pytest.mark.usefixtures('models', 'search_lib')


@uriinfo_fixtures
def test_uriinfo_returns_number_from_search_lib(search_lib):
    request = mock.Mock(params={'uri': 'test_uri'})
    search_lib.search.return_value = {'total': 29}

    result = views.uriinfo(request)

    search_lib.search.assert_called_once_with(
        request, {'uri': 'test_uri', 'limit': 0})
    assert result['total'] == search_lib.search.return_value['total']


@uriinfo_fixtures
def test_uriinfo_returns_blocked_from_model(models):
    request = mock.Mock(params={'uri': 'test_uri'})

    result = views.uriinfo(request)

    models.Blocklist.is_blocked.assert_called_once_with('test_uri')
    assert result['blocked'] == models.Blocklist.is_blocked.return_value


@uriinfo_fixtures
def test_uriinfo_raises_if_no_uri():
    with pytest.raises(httpexceptions.HTTPBadRequest):
        views.uriinfo(mock.Mock(params={}))


@pytest.fixture
def models(config, request):  # pylint:disable=unused-argument
    patcher = mock.patch('h.blocklist.views.models', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def search_lib(config, request):  # pylint:disable=unused-argument
    patcher = mock.patch('h.blocklist.views.search_lib', autospec=True)
    request.addfinalizer(patcher.stop)
    return patcher.start()
