# -*- coding: utf-8 -*-

import pytest

from h import tweens
from h.util.redirects import Redirect


def test_tween_redirect_loads_redirects(patch):
    open_ = patch('h.tweens.open')
    parse_redirects = patch('h.tweens.parse_redirects')

    tweens.redirect_tween_factory(handler=None, registry=None)

    open_.assert_called_once_with('h/redirects', encoding='utf-8')
    # Parse redirects is called with the value returned by the context manager
    parse_redirects.assert_called_once_with(open_.return_value.__enter__.return_value)


def test_tween_redirect_non_redirected_route(pyramid_request):
    redirects = [
        Redirect(src='/foo', dst='http://bar', internal=False, prefix=False)
    ]

    pyramid_request.path = '/quux'

    tween = tweens.redirect_tween_factory(
        lambda req: req.response,
        pyramid_request.registry,
        redirects)

    response = tween(pyramid_request)

    assert response.status_code == 200


def test_tween_redirect_redirected_route(pyramid_request, pyramid_config):
    redirects = [
        Redirect(src='/foo', dst='http://bar', internal=False, prefix=False)
    ]

    pyramid_request.path = '/foo'

    tween = tweens.redirect_tween_factory(
        lambda req: req.response,
        pyramid_request.registry,
        redirects)

    response = tween(pyramid_request)

    assert response.status_code == 301
    assert response.location == 'http://bar'


def test_tween_security_header_adds_headers(pyramid_request):
    tween = tweens.security_header_tween_factory(lambda req: req.response,
                                                 pyramid_request.registry)

    response = tween(pyramid_request)

    assert response.headers['Referrer-Policy'] == 'origin-when-cross-origin, strict-origin-when-cross-origin'
    assert response.headers['X-XSS-Protection'] == '1; mode=block'


@pytest.mark.parametrize('content_type, expected_cc_header', [
    # Web pages.
    ('text/html', None),

    # An API or XHR response.
    ('application/json', 'no-cache'),

    # A response with no content (eg. 204 response to a `DELETE` request).
    (None, None),
])
def test_tween_cache_header_adds_headers(pyramid_request, content_type, expected_cc_header):
    tween = tweens.cache_header_tween_factory(lambda req: req.response,
                                              pyramid_request.registry)

    if content_type is not None:
        pyramid_request.response.headers['Content-Type'] = content_type

    response = tween(pyramid_request)

    assert response.headers.get('Cache-Control') == expected_cc_header
