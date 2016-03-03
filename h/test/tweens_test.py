# -*- coding: utf-8 -*-

from pyramid.testing import DummyRequest
from h import tweens


def test_tween_csp_default_headers():
    request = DummyRequest()
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    assert 'Content-Security-Policy-Report-Only' not in response.headers
    assert 'Content-Security-Policy' in response.headers


def test_tween_csp_report_only_headers():
    request = DummyRequest()
    request.registry.settings = {'csp.report_only': True}
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    assert 'Content-Security-Policy-Report-Only' in response.headers
    assert 'Content-Security-Policy' not in response.headers


def test_tween_csp_uri():
    request = DummyRequest()
    request.registry.settings = {'csp': {'report-uri': ['localhost']}}
    tween = tweens.content_security_policy_tween_factory(
        lambda req: req.response,
        request.registry)

    response = tween(request)

    assert 'report-uri localhost' in response.headers['Content-Security-Policy']
