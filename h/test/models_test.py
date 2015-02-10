# -*- coding: utf-8 -*-
import unittest

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
