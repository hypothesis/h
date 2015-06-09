from mock import MagicMock
import pytest

from webob import Request
from webob.exc import HTTPBadRequest

from h.api.middleware import permit_cors


# ARGHY ARGHY ARGHSTICKS.
#
# BEWARE. You might think that the lovely WebOb would treat
#
#    resp = app(request)
#
# and
#
#    resp = request.get_response(app)
#
# identically. But unfortunately this isn't the case. Specifically, in
# WebOb==1.4 additional arguments to be passed to the middleware callable are
# lost with the first pattern, but preserved with the second. That is, if you
# create a wrapped application with:
#
#    app = my_middleware(app, some_kwarg=True)
#
# Then when you run
#
#    resp = app(request)
#
# you will expect the underlying `my_middleware` callable to be passed
# `some_kwarg=True`, but it won't be, and you will waste a couple of hours
# trying to work out what you did wrong.
#
# Don't do that.
#
# - NS, 2015-06-09


def test_permit_cors_passes_through_non_preflight():
    request = Request.blank('/')
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.body == 'OK'
    assert resp.status_code == 200


def test_permit_cors_adds_allow_origin_header_for_non_preflight():
    request = Request.blank('/', )
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.headers['Access-Control-Allow-Origin'] == '*'


def test_permit_cors_400s_for_preflight_without_origin(headers):
    del headers['Origin']
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.status_code == 400


def test_permit_cors_400s_for_preflight_without_reqmethod(headers):
    del headers['Access-Control-Request-Method']
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.status_code == 400


def test_permit_cors_returns_empty_body_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.body == ''


def test_permit_cors_sets_allow_origin_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.headers['Access-Control-Allow-Origin'] == 'http://example.com'


def test_permit_cors_sets_allow_methods_OPTIONS_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.headers['Access-Control-Allow-Methods'] == 'OPTIONS'


def test_permit_cors_sets_allow_methods_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp, allow_methods=('PUT', 'DELETE'))

    resp = request.get_response(wrapped)
    values = resp.headers['Access-Control-Allow-Methods'].split(', ')

    assert sorted(values) == ['DELETE', 'OPTIONS', 'PUT']


def test_permit_cors_sets_allow_credentials_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp, allow_credentials=True)

    resp = request.get_response(wrapped)

    assert resp.headers['Access-Control-Allow-Credentials'] == 'true'


def test_permit_cors_sets_allow_headers_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp, allow_headers=('Foo', 'X-Bar'))

    resp = request.get_response(wrapped)
    values = resp.headers['Access-Control-Allow-Headers'].split(', ')

    assert sorted(values) == ['Foo', 'X-Bar']


def test_permit_cors_sets_expose_headers_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp, expose_headers=('Foo', 'X-Bar'))

    resp = request.get_response(wrapped)
    values = resp.headers['Access-Control-Expose-Headers'].split(', ')

    assert sorted(values) == ['Foo', 'X-Bar']


def test_permit_cors_sets_max_age_default_for_preflight(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp)

    resp = request.get_response(wrapped)

    assert resp.headers['Access-Control-Max-Age'] == '86400'


def test_permit_cors_sets_max_age_for_preflight_when_set(headers):
    request = Request.blank('/', method='OPTIONS', headers=headers)
    wrapped = permit_cors(wsgi_testapp, max_age=42)

    resp = request.get_response(wrapped)

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
