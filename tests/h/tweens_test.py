# -*- coding: utf-8 -*-

import mock

from h import tweens


def test_tween_csp_noop_by_default(pyramid_request):
    handler = mock.sentinel.HANDLER
    result = tweens.content_security_policy_tween_factory(handler,
                                                          pyramid_request.registry)

    assert result == handler


def test_tween_csp_default_headers(pyramid_request):
    pyramid_request.registry.settings['csp.enabled'] = True
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        pyramid_request.registry)

    response = tween(pyramid_request)

    assert 'Content-Security-Policy-Report-Only' not in response.headers
    assert 'Content-Security-Policy' in response.headers


def test_tween_csp_report_only_headers(pyramid_request):
    pyramid_request.registry.settings.update({
        'csp.enabled': True,
        'csp.report_only': True,
    })
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        pyramid_request.registry)

    response = tween(pyramid_request)

    assert 'Content-Security-Policy-Report-Only' in response.headers
    assert 'Content-Security-Policy' not in response.headers


def test_tween_csp_uri(pyramid_request):
    pyramid_request.registry.settings.update({
        'csp.enabled': True,
        'csp.report_only': False,
        'csp': {'report-uri': ['localhost']},
    })
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        pyramid_request.registry)

    response = tween(pyramid_request)

    expected = 'report-uri localhost'
    assert expected == response.headers['Content-Security-Policy']


def test_tween_csp_header(pyramid_request):
    pyramid_request.registry.settings.update({
        "csp.enabled": True,
        "csp.report_only": False,
        "csp": {
            "font-src": ["'self'", "fonts.gstatic.com"],
            "report-uri": ['localhost'],
            "script-src": ["'self'"],
            "style-src": ["'self'", "fonts.googleapis.com"],
        },
    })
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        pyramid_request.registry)

    response = tween(pyramid_request)

    expected = "font-src 'self' fonts.gstatic.com; report-uri localhost; " \
        "script-src 'self'; style-src 'self' fonts.googleapis.com"

    assert expected == response.headers['Content-Security-Policy']


def test_tween_redirect_non_redirected_route(pyramid_request):
    redirects = [('/foo', 'bar')]

    pyramid_request.path = '/quux'

    tween = tweens.redirect_tween_factory(
        lambda req: req.response,
        pyramid_request.registry,
        redirects)

    response = tween(pyramid_request)

    assert response.status_code == 200


def test_tween_redirect_redirected_route(pyramid_request, pyramid_config):
    redirects = [('/foo', 'bar')]

    pyramid_config.add_route('bar', '/bar')

    pyramid_request.path = '/foo'

    tween = tweens.redirect_tween_factory(
        lambda req: req.response,
        pyramid_request.registry,
        redirects)

    response = tween(pyramid_request)

    assert response.status_code == 301
    assert response.location == 'http://example.com/bar'


def test_tween_redirect_matches_prefixes(pyramid_request, pyramid_config):
    redirects = [('/foo', 'bar')]

    pyramid_config.add_route('bar', '/bar')

    pyramid_request.path = '/foo/baz'

    tween = tweens.redirect_tween_factory(
        lambda req: req.response,
        pyramid_request.registry,
        redirects)

    response = tween(pyramid_request)

    assert response.status_code == 301
    assert response.location == 'http://example.com/bar/baz'


def test_tween_redirect_matches_in_order(pyramid_request, pyramid_config):
    redirects = [
        ('/foo/bar', 'bar'),
        ('/foo', 'foonew'),
    ]

    pyramid_config.add_route('bar', '/bar')
    pyramid_config.add_route('foonew', '/foonew')

    pyramid_request.path = '/foo/bar'

    tween = tweens.redirect_tween_factory(
        lambda req: req.response,
        pyramid_request.registry,
        redirects)

    response = tween(pyramid_request)

    assert response.status_code == 301
    assert response.location == 'http://example.com/bar'
