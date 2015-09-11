import mock
from pyramid import security

from h.api import resources


class TestAnnotations(object):

    def test__acl__when_request_has_no_json_body(self):
        request = mock.Mock()
        # Make request.json_body raise ValueError.
        type(request).json_body = mock.PropertyMock(side_effect=ValueError)
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Deny, security.Everyone, 'create')]

    def test__acl__when_request_contains_no_group(self):
        request = mock.Mock()
        request.json_body = {}
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, 'group:__world__', 'create'),
            (security.Deny, security.Everyone, 'create')]

    def test__acl__when_request_has_a_group(self):
        request = mock.Mock()
        request.json_body = {'group': 'xyzabc'}
        annotations = resources.Annotations(request)

        assert annotations.__acl__() == [
            (security.Allow, 'group:xyzabc', 'create'),
            (security.Deny, security.Everyone, 'create')]
