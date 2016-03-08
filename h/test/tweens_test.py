# -*- coding: utf-8 -*-

import mock
from pyramid.testing import DummyRequest

from h import tweens


def test_tween_csp_noop_by_default():
    request = DummyRequest()
    handler = mock.sentinel.HANDLER
    result = tweens.content_security_policy_tween_factory(handler,
                                                          request.registry)

    assert result == handler


def test_tween_csp_default_headers():
    request = DummyRequest()
    request.registry.settings['csp.enabled'] = True
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    assert 'Content-Security-Policy-Report-Only' not in response.headers
    assert 'Content-Security-Policy' in response.headers


def test_tween_csp_report_only_headers():
    request = DummyRequest()
    request.registry.settings.update({
        'csp.enabled': True,
        'csp.report_only': True,
    })
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    assert 'Content-Security-Policy-Report-Only' in response.headers
    assert 'Content-Security-Policy' not in response.headers


def test_tween_csp_uri():
    request = DummyRequest()
    request.registry.settings.update({
        'csp.enabled': True,
        'csp': {'report-uri': ['localhost']},
    })
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    expected = 'report-uri localhost'
    assert expected == response.headers['Content-Security-Policy']


def test_tween_csp_header():
    request = DummyRequest()
    request.registry.settings.update({
        "csp.enabled": True,
        "csp": {
            "font-src": ["'self'", "fonts.gstatic.com"],
            "report-uri": ['localhost'],
            "script-src": ["'self'"],
            "style-src": ["'self'", "fonts.googleapis.com"],
        },
    })
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    expected = "font-src 'self' fonts.gstatic.com; report-uri localhost; " \
        "script-src 'self'; style-src 'self' fonts.googleapis.com"

    assert expected == response.headers['Content-Security-Policy']
