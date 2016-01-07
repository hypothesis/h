import mock
from pytest import raises
from pyramid import security

from h.api import resources


class TestAnnotationPermissions(object):

    def test_principal(self):
        resource = resources.Annotation('foo', {
            'permissions': {
                'read': ['saoirse'],
            }
        })
        actual = resource.__acl__()
        expect = [(security.Allow, 'saoirse', 'read')]
        assert actual == expect

    def test_deny_system_role(self):
        resource = resources.Annotation('foo', {
            'permissions': {
                'read': [security.Everyone],
            }
        })
        actual = resource.__acl__()
        expect = []
        assert actual == expect

    def test_group(self):
        resource = resources.Annotation('foo', {
            'permissions': {
                'read': ['group:lulapalooza'],
            }
        })
        actual = resource.__acl__()
        expect = [(security.Allow, 'group:lulapalooza', 'read')]
        assert actual == expect

    def test_group_world(self):
        resource = resources.Annotation('foo', {
            'permissions': {
                'read': ['group:__world__'],
            }
        })
        actual = resource.__acl__()
        expect = [(security.Allow, security.Everyone, 'read')]
        assert actual == expect

    def test_group_authenticated(self):
        resource = resources.Annotation('foo', {
            'permissions': {
                'read': ['group:__authenticated__'],
            }
        })
        actual = resource.__acl__()
        expect = [(security.Allow, security.Authenticated, 'read')]
        assert actual == expect


class TestAnnotationsPermissions(object):

    def test_when_request_has_no_json_body(self):
        request = mock.Mock()
        # Make request.json_body raise ValueError.
        type(request).json_body = mock.PropertyMock(side_effect=ValueError)
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, security.Authenticated, 'create'),
            (security.Deny, security.Everyone, 'create')]

    def test_when_request_has_non_object_body(self):
        request = mock.Mock()
        request.json_body = "flibble"
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, security.Authenticated, 'create'),
            (security.Deny, security.Everyone, 'create')]

    def test_when_request_contains_no_group(self):
        request = mock.Mock()
        request.json_body = {}
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, security.Authenticated, 'create'),
            (security.Deny, security.Everyone, 'create')]

    def test_when_request_has_a_group(self):
        request = mock.Mock()
        request.json_body = {'group': 'xyzabc'}
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, 'group:xyzabc', 'create'),
            (security.Deny, security.Everyone, 'create')]

    def test_when_request_has_group_world(self):
        request = mock.Mock()
        request.json_body = {'group': '__world__'}
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, security.Authenticated, 'create'),
            (security.Deny, security.Everyone, 'create')]
