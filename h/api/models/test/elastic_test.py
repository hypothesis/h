# -*- coding: utf-8 -*-

import pytest
from mock import patch
from mock import PropertyMock

from pyramid import security

from h.api.models.elastic import Annotation


def test_uri():
    assert Annotation(uri="http://foo.com").uri == "http://foo.com"


def test_uri_with_no_uri():
    assert Annotation().uri == ""


def test_uri_when_uri_is_not_a_string():
    for uri in (True, None, 23, 23.7, {"foo": False}, [1, 2, 3]):
        assert isinstance(Annotation(uri=uri).uri, unicode)


def test_target_links_from_annotation():
    annotation = Annotation(target=[{'source': 'target link'}])
    assert annotation.target_links == ['target link']


def test_parent_id_returns_none_if_no_references():
    annotation = Annotation()
    assert annotation.parent_id is None


def test_parent_id_returns_none_if_empty_references():
    annotation = Annotation(references=[])
    assert annotation.parent_id is None


def test_parent_id_returns_none_if_references_not_list():
    annotation = Annotation(references={'foo': 'bar'})
    assert annotation.parent_id is None


def test_parent_id_returns_thread_parent_id():
    annotation = Annotation(references=['abc123', 'def456'])
    assert annotation.parent_id == 'def456'


def test_acl_principal():
    annotation = Annotation({
        'permissions': {
            'read': ['saoirse'],
        }
    })
    actual = annotation.__acl__()
    expect = [(security.Allow, 'saoirse', 'read'), security.DENY_ALL]
    assert actual == expect


def test_acl_deny_system_role():
    annotation = Annotation({
        'permissions': {
            'read': [security.Everyone],
        }
    })
    actual = annotation.__acl__()
    expect = [security.DENY_ALL]
    assert actual == expect


def test_acl_group():
    annotation = Annotation({
        'permissions': {
            'read': ['group:lulapalooza'],
        }
    })
    actual = annotation.__acl__()
    expect = [(security.Allow, 'group:lulapalooza', 'read'), security.DENY_ALL]
    assert actual == expect


def test_acl_group_world():
    annotation = Annotation({
        'permissions': {
            'read': ['group:__world__'],
        }
    })
    actual = annotation.__acl__()
    expect = [(security.Allow, security.Everyone, 'read'), security.DENY_ALL]
    assert actual == expect


def test_acl_group_authenticated():
    annotation = Annotation({
        'permissions': {
            'read': ['group:__authenticated__'],
        }
    })
    actual = annotation.__acl__()
    expect = [(security.Allow, security.Authenticated, 'read'),
              security.DENY_ALL]
    assert actual == expect


@pytest.fixture
def link_text(request):
    patcher = patch('h.api.models.elastic.Annotation.link_text',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def title(request):
    patcher = patch('h.api.models.elastic.Annotation.title',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def href(request):
    patcher = patch('h.api.models.elastic.Annotation.href',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def hostname_or_filename(request):
    patcher = patch('h.api.models.elastic.Annotation.hostname_or_filename',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()
