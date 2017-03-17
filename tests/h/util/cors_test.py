# -*- coding: utf-8 -*-
import mock
import pytest

from pyramid.request import Request
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest

from h.util.cors import policy, set_cors_headers


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


def test_cors_sets_allow_methods_OPTIONS_for_preflight(headers):
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

    def test_it_calls_wrapped_view_for_preflight_request_when_disabled(self,
                                                                       pyramid_request,
                                                                       testview):
        cors_policy = policy(allow_preflight=False)
        pyramid_request.request_method = 'OPTIONS'

        cors_policy(testview)(None, pyramid_request)

        assert testview.called

    def test_it_skips_wrapped_view_for_preflight_request_when_enabled(self,
                                                                      pyramid_request,
                                                                      testview):
        cors_policy = policy(allow_preflight=True)
        pyramid_request.method = 'OPTIONS'
        pyramid_request.headers['Origin'] = 'https://example.org'
        pyramid_request.headers['Access-Control-Request-Method'] = 'GET'

        cors_policy(testview)(None, pyramid_request)

        assert not testview.called

    def test_it_returns_empty_response_for_preflight_request_when_enabled(self,
                                                                          pyramid_request,
                                                                          testview):
        cors_policy = policy(allow_preflight=True)
        pyramid_request.method = 'OPTIONS'
        pyramid_request.headers['Origin'] = 'https://example.org'
        pyramid_request.headers['Access-Control-Request-Method'] = 'GET'

        response = cors_policy(testview)(None, pyramid_request)

        assert response.body == ''

    def test_it_sets_cors_headers(self, pyramid_request, testview, set_cors_headers):
        cors_policy = policy()

        cors_policy(testview)(None, pyramid_request)

        assert set_cors_headers.called

    def test_it_returns_set_cors_headers_value(self, pyramid_request, testview, set_cors_headers):
        cors_policy = policy()

        response = cors_policy(testview)(None, pyramid_request)

        assert response == set_cors_headers.return_value

    def test_it_sets_cors_headers_for_preflight_request_when_enabled(self,
                                                                     pyramid_request,
                                                                     testview,
                                                                     set_cors_headers):
        cors_policy = policy(allow_preflight=True)
        pyramid_request.method = 'OPTIONS'
        pyramid_request.headers['Origin'] = 'https://example.org'
        pyramid_request.headers['Access-Control-Request-Method'] = 'GET'

        cors_policy(testview)(None, pyramid_request)

        assert set_cors_headers.called

    def test_it_returns_set_cors_headers_value_for_preflight_request_when_enabled(
            self, pyramid_request, testview, set_cors_headers):
        cors_policy = policy(allow_preflight=True)
        pyramid_request.method = 'OPTIONS'
        pyramid_request.headers['Origin'] = 'https://example.org'
        pyramid_request.headers['Access-Control-Request-Method'] = 'GET'

        response = cors_policy(testview)(None, pyramid_request)

        assert response == set_cors_headers.return_value

    @pytest.fixture
    def testview(self):
        return mock.Mock(return_value=Response('OK'))

    @pytest.fixture
    def set_cors_headers(self, patch):
        return patch('h.util.cors.set_cors_headers')


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
