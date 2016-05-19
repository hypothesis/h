# -*- coding: utf-8 -*-
import pytest

from pyramid.request import Request
from pyramid.httpexceptions import HTTPBadRequest

from h.api.cors import set_cors_headers


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
