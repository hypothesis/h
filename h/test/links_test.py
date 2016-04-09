# -*- coding: utf-8 -*-

from pyramid.testing import DummyRequest
import pytest

from h import links

class FakeAnnotation(object):
    def __init__(self):
        self.id = '123'
        self.references = None
        self.target_uri = 'http://example.com/foo/bar'


def test_incontext_link(api_request):
    annotation = FakeAnnotation()

    link = links.incontext_link(api_request, annotation)

    assert link == 'https://hyp.is/123/example.com/foo/bar'


def test_incontext_link_is_none_for_replies(api_request):
    annotation = FakeAnnotation()
    annotation.references = ['parent']

    link = links.incontext_link(api_request, annotation)

    assert link is None


@pytest.mark.parametrize('target_uri,expected', [
    (None, 'https://hyp.is/123'),
    ('', 'https://hyp.is/123'),
    ('something_not_a_url', 'https://hyp.is/123'),
    ('ftp://not_http', 'https://hyp.is/123'),
    ('http://example.com/foo/bar', 'https://hyp.is/123/example.com/foo/bar'),
    ('https://safari.org/giraffes', 'https://hyp.is/123/safari.org/giraffes'),
])
def test_incontext_link_appends_schemaless_uri_if_present(api_request,
                                                          target_uri,
                                                          expected):
    annotation = FakeAnnotation()
    annotation.target_uri = target_uri

    link = links.incontext_link(api_request, annotation)

    assert link == expected


@pytest.fixture
def api_request():
    def feature(name):
        return name == 'direct_linking'
    request = DummyRequest(feature=feature)
    request.registry.settings = {'h.bouncer_url': 'https://hyp.is'}
    return request
