# -*- coding: utf-8 -*-

from h import tweens


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


def test_tween_security_header_adds_headers(pyramid_request):
    tween = tweens.security_header_tween_factory(lambda req: req.response,
                                                 pyramid_request.registry)

    response = tween(pyramid_request)

    assert response.headers['Referrer-Policy'] == 'origin-when-cross-origin'
    assert response.headers['X-XSS-Protection'] == '1; mode=block'
