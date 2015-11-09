# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
import itertools
import re
import urllib

import jinja2
import pytest
from mock import patch
from mock import PropertyMock

from h.api import models

analysis = models.Annotation.__analysis__


def test_strip_scheme_char_filter():
    f = analysis['char_filter']['strip_scheme']
    p = f['pattern']
    r = f['replacement']
    assert(re.sub(p, r, 'http://ping/pong#hash') == 'ping/pong#hash')
    assert(re.sub(p, r, 'chrome-extension://1234/a.js') == '1234/a.js')
    assert(re.sub(p, r, 'a+b.c://1234/a.js') == '1234/a.js')
    assert(re.sub(p, r, 'uri:x-pdf:1234') == 'x-pdf:1234')
    assert(re.sub(p, r, 'example.com') == 'example.com')
    # This is ambiguous, and possibly cannot be expected to work.
    # assert(re.sub(p, r, 'localhost:5000') == 'localhost:5000')


def test_path_url_filter():
    patterns = analysis['filter']['path_url']['patterns']
    assert(captures(patterns, 'example.com/foo/bar?query#hash') == [
        'example.com/foo/bar'
    ])
    assert(captures(patterns, 'example.com/foo/bar/') == [
        'example.com/foo/bar/'
    ])


def test_rstrip_slash_filter():
    p = analysis['filter']['rstrip_slash']['pattern']
    r = analysis['filter']['rstrip_slash']['replacement']
    assert(re.sub(p, r, 'example.com/') == 'example.com')
    assert(re.sub(p, r, 'example.com/foo/bar/') == 'example.com/foo/bar')


def test_uri_part_tokenizer():
    text = 'http://a.b/foo/bar?c=d#stuff'
    pattern = analysis['tokenizer']['uri_part']['pattern']
    assert(re.split(pattern, text) == [
        'http', '', '', 'a', 'b', 'foo', 'bar', 'c', 'd', 'stuff'
    ])

    text = urllib.quote_plus(text)
    assert(re.split(pattern, 'http://jump.to/?u=' + text) == [
        'http', '', '', 'jump', 'to', '', 'u',
        'http', '', '', 'a', 'b', 'foo', 'bar', 'c', 'd', 'stuff'
    ])


def captures(patterns, text):
    return list(itertools.chain(*(groups(p, text) for p in patterns)))


def groups(pattern, text):
    return re.search(pattern, text).groups() or []


def test_uri():
    assert models.Annotation(uri="http://foo.com").uri == "http://foo.com"


def test_uri_with_no_uri():
    assert models.Annotation().uri == ""


def test_uri_when_uri_is_not_a_string():
    for uri in (True, None, 23, 23.7, {"foo": False}, [1, 2, 3]):
        assert isinstance(models.Annotation(uri=uri).uri, unicode)


def test_target_links_from_annotation():
    annotation = models.Annotation(target=[{'source': 'target link'}])
    assert annotation.target_links == ['target link']


def test_parent_returns_none_if_no_references():
    annotation = models.Annotation()
    assert annotation.parent is None


def test_parent_returns_none_if_empty_references():
    annotation = models.Annotation(references=[])
    assert annotation.parent is None


def test_parent_returns_none_if_references_not_list():
    annotation = models.Annotation(references={'foo': 'bar'})
    assert annotation.parent is None


@patch.object(models.Annotation, 'fetch', spec=True)
def test_parent_fetches_thread_parent(fetch):
    annotation = models.Annotation(references=['abc123', 'def456'])
    annotation.parent
    fetch.assert_called_with('def456')


@patch.object(models.Annotation, 'fetch', spec=True)
def test_parent_returns_thread_parent(fetch):
    annotation = models.Annotation(references=['abc123', 'def456'])
    parent = annotation.parent
    assert parent == fetch.return_value


@pytest.fixture
def link_text(request):
    patcher = patch('h.api.models.Annotation.link_text',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def title(request):
    patcher = patch('h.api.models.Annotation.title',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()

@pytest.fixture
def href(request):
    patcher = patch('h.api.models.Annotation.href',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


@pytest.fixture
def hostname_or_filename(request):
    patcher = patch('h.api.models.Annotation.hostname_or_filename',
                    new_callable=PropertyMock)
    request.addfinalizer(patcher.stop)
    return patcher.start()


