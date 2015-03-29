# -*- coding: utf-8 -*-
import unittest

from pytest import fixture, raises
from pyramid import security
import re

from h import models


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
index_patterns = analysis['filter']['uri_index']['patterns']
search_patterns = analysis['filter']['uri_search']['patterns']


def test_uri_search_indexes_hash_variants():
    caps = _pattern_captures(index_patterns, 'http://example.com/page#hash')

    assert 'example.com/page' in caps


def test_uri_search_searches_hash_variants():
    caps = _pattern_captures(search_patterns, 'http://example.com/page#hash')

    assert 'example.com/page' in caps


# Simulate the ElasticSearch pattern_capture filter!
def _pattern_captures(patterns, uri):
    result = []
    patterns_re = [re.compile(p) for p in patterns]
    for p in patterns_re:
        m = p.search(uri)
        if m is not None:
            result.append(m.group(1))
    return result

