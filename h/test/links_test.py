# -*- coding: utf-8 -*-

from pyramid.testing import DummyRequest
from mock import Mock
import pytest

from h import links


def test_incontext_link(api_request):
    annotation = Mock()
    annotation.id = '123'
    annotation.references = None

    assert links.incontext_link(api_request, annotation) == 'https://hyp.is/123'


@pytest.fixture
def api_request():
    def feature(name):
        return name == 'direct_linking'
    request = DummyRequest(feature=feature)
    request.registry.settings = {'h.bouncer_url': 'https://hyp.is'}
    return request
