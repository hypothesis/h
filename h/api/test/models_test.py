# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
import itertools
import re
import unittest
import urllib

from pytest import raises
from pyramid import security

from h.api import models


class TestAnnotationPermissions(unittest.TestCase):
    def test_principal(self):
        annotation = models.Annotation()
        annotation['permissions'] = {
            'read': ['saoirse'],
        }
        actual = annotation.__acl__()
        expect = [(security.Allow, 'saoirse', 'read')]
        assert actual == expect

    def test_admin_party(self):
        annotation = models.Annotation()
        actual = annotation.__acl__()
        expect = [(security.Allow, security.Everyone, security.ALL_PERMISSIONS)]
        assert actual == expect

    def test_deny_system_role(self):
        annotation = models.Annotation()
        annotation['permissions'] = {
            'read': [security.Everyone],
        }
        with raises(ValueError):
            annotation.__acl__()

    def test_group(self):
        annotation = models.Annotation()
        annotation['permissions'] = {
            'read': ['group:lulapalooza'],
        }
        actual = annotation.__acl__()
        expect = [(security.Allow, 'group:lulapalooza', 'read')]
        assert actual == expect

    def test_group_world(self):
        annotation = models.Annotation()
        annotation['permissions'] = {
            'read': ['group:__world__'],
        }
        actual = annotation.__acl__()
        expect = [(security.Allow, security.Everyone, 'read')]
        assert actual == expect

    def test_group_authenticated(self):
        annotation = models.Annotation()
        annotation['permissions'] = {
            'read': ['group:__authenticated__'],
        }
        actual = annotation.__acl__()
        expect = [(security.Allow, security.Authenticated, 'read')]
        assert actual == expect


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


def test_title_with_a_document_that_has_a_title():
    annotation = models.Annotation(document={'title': 'document title'})
    assert annotation.title == 'document title'


def test_title_with_a_document_that_has_no_title():
    annotation = models.Annotation(document={})
    assert annotation.title == ''


def test_title_annotation_that_has_no_document():
    assert models.Annotation().title == ''


def test_description():
    annotation = models.Annotation(
        target=[{'selector': [{'exact': 'selected text'}]}],
        text='entered text'
    )

    assert annotation.description == (
        "&lt;blockquote&gt;selected text&lt;/blockquote&gt;entered text")


def test_created_day_string_from_annotation():
    annotation = models.Annotation(created='2015-09-04T17:37:49.517852+00:00')
    assert annotation.created_day_string == '2015-09-04'


def test_target_links_from_annotation():
    annotation = models.Annotation(target=[{'source': 'target link'}])
    assert annotation.target_links == ['target link']
