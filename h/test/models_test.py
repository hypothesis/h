# -*- coding: utf-8 -*-
import unittest
import pytest

from pytest import fixture, raises
from pyramid import security

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


@pytest.mark.usefixtures('es_connection')
def test_uri_mapping():
    permissions = {
        'read': ['group:__world__'],
    }
    a1 = models.Annotation(uri='http://example.com/page#hashtag',
                           permissions=permissions)
    a1.save()
    a2 = models.Annotation(uri='http://example.com/page',
                           permissions=permissions)
    a2.save()
    a3 = models.Annotation(uri='http://totallydifferent.domain.com/',
                           permissions=permissions)
    a3.save()

    res = models.Annotation.search(query={'uri': 'example.com/page'})
    assert len(res) == 2
