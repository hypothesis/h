# -*- coding: utf-8 -*-
import mock
import pytest

from pyramid.request import Request
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest

from h.util.cors import add_preflight_view, policy, set_cors_headers


def test_cors_passes_through_non_preflight():
    request = Request.blank('/')

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp)

    assert resp.body == 'OK'
    assert resp.status_code == 200


def test_cors_adds_allow_origin_header_for_non_preflight():
    request = Request.blank('/', )

    resp = request.get_response(wsgi_testapp)
    set_cors_headers(request, resp)

    assert resp.headers['Access-Control-Allow-Origin'] == '*'


def test_cors_400s_for_preflight_without_origin(headers):
    del headers['Origin']
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)

    with pytest.raises(HTTPBadRequest):
        set_cors_headers(request, resp)


def test_cors_400s_for_preflight_without_reqmethod(headers):
    del headers['Access-Control-Request-Method']
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)

    with pytest.raises(HTTPBadRequest):
        set_cors_headers(request, resp)


def test_cors_sets_allow_origin_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp)

    assert resp.headers['Access-Control-Allow-Origin'] == 'http://example.com'


def test_cors_sets_allow_methods_OPTIONS_for_preflight(headers):  # noqa
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp)

    assert resp.headers['Access-Control-Allow-Methods'] == 'OPTIONS'


def test_cors_sets_allow_methods_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp, allow_methods=('PUT', 'DELETE'))
    values = resp.headers['Access-Control-Allow-Methods'].split(', ')

    assert sorted(values) == ['DELETE', 'OPTIONS', 'PUT']


def test_cors_sets_allow_credentials_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp, allow_credentials=True)

    assert resp.headers['Access-Control-Allow-Credentials'] == 'true'


def test_cors_sets_allow_headers_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp, allow_headers=('Foo', 'X-Bar'))
    values = resp.headers['Access-Control-Allow-Headers'].split(', ')

    assert sorted(values) == ['Foo', 'X-Bar']


def test_cors_sets_expose_headers_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp, expose_headers=('Foo', 'X-Bar'))
    values = resp.headers['Access-Control-Expose-Headers'].split(', ')

    assert sorted(values) == ['Foo', 'X-Bar']


def test_cors_sets_max_age_default_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp)

    assert resp.headers['Access-Control-Max-Age'] == '86400'


def test_cors_sets_max_age_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)

    resp = request.get_response(wsgi_testapp)
    resp = set_cors_headers(request, resp, max_age=42)

    assert resp.headers['Access-Control-Max-Age'] == '42'


class TestCorsViewDecorator(object):
    def test_it_calls_wrapped_view_function(self, pyramid_request, testview):
        cors_policy = policy()

        cors_policy(testview)(None, pyramid_request)

        assert testview.called

    def test_it_returns_wrapped_view_function_response(self, pyramid_request, testview):
        cors_policy = policy()

        response = cors_policy(testview)(None, pyramid_request)

        assert response.body == 'OK'

    def test_it_sets_cors_headers(self, pyramid_request, testview, set_cors_headers):
        cors_policy = policy()

        cors_policy(testview)(None, pyramid_request)

        assert set_cors_headers.called

    def test_it_returns_set_cors_headers_value(self, pyramid_request, testview, set_cors_headers):
        cors_policy = policy()

        response = cors_policy(testview)(None, pyramid_request)

        assert response == set_cors_headers.return_value

    @pytest.fixture
    def testview(self):
        return mock.Mock(return_value=Response('OK'))

    @pytest.fixture
    def set_cors_headers(self, patch):
        return patch('h.util.cors.set_cors_headers')


class TestAddPreflightView(object):

    def test_it_adds_preflight_view(self, pyramid_config):
        def view(request):
            pass  # noop
        cors_policy = policy()
        pyramid_config.add_route('api.read_thing', '/api/thing')
        add_preflight_view(pyramid_config, 'api.read_thing', cors_policy)
        app = pyramid_config.make_wsgi_app()

        headers = {'Origin': 'https://custom-client.herokuapp.com',
                   'Access-Control-Request-Method': 'POST'}
        request = Request.blank('/api/thing', method='OPTIONS', headers=headers)
        resp = request.get_response(app)

        assert resp.status_code == 200
        assert resp.body == ''

    def test_preflight_view_uses_cors_decorator(self, pyramid_config):
        def view(request):
            pass  # noop
        cors_policy = policy()
        pyramid_config.add_route('api.read_thing', '/api/thing')
        pyramid_config.add_view = mock.Mock()

        add_preflight_view(pyramid_config, 'api.read_thing', cors_policy)

        (_, kwargs) = pyramid_config.add_view.call_args
        assert kwargs['decorator'] == cors_policy

    def test_it_adds_one_preflight_view_per_route(self, pyramid_config):
        cors_policy = policy()
        pyramid_config.add_route('api.read_thing', '/api/thing')
        pyramid_config.add_view = mock.Mock()

        def view(request):
            pass  # noop

        add_preflight_view(pyramid_config, 'api.read_thing', cors_policy)
        add_preflight_view(pyramid_config, 'api.read_thing', cors_policy)

        assert pyramid_config.add_view.call_count == 1


# A tiny WSGI application used for testing the middleware
def wsgi_testapp(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ['OK']


@pytest.fixture
def headers():
    return {
        'Origin': 'http://example.com',
        'Access-Control-Request-Method': 'PUT',
        'Access-Control-Request-Headers': 'Authorization',
    }
