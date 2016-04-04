# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
from pyramid import testing
from pyramid import security
import pytest

from h.api import schemas


class ExampleSchema(schemas.JSONSchema):
    schema = {
        b'$schema': b'http://json-schema.org/draft-04/schema#',
        b'type': b'string',
    }


class TestJSONSchema(object):

    def test_it_returns_data_when_valid(self):
        data = "a string"

        assert ExampleSchema().validate(data) == data

    def test_it_raises_when_data_invalid(self):
        data = 123  # not a string

        with pytest.raises(schemas.ValidationError):
            ExampleSchema().validate(data)

    def test_it_sets_appropriate_error_message_when_data_invalid(self):
        data = 123  # not a string

        with pytest.raises(schemas.ValidationError) as e:
            ExampleSchema().validate(data)

        message = e.value.message
        assert message.startswith("123 is not of type 'string'")


class TestCreateAnnotationSchema(object):

    def test_it_passes_input_to_structure_validator(self):
        request = testing.DummyRequest()
        schema = schemas.CreateAnnotationSchema(request)
        schema.structure = mock.Mock()
        schema.structure.validate.return_value = {}

        schema.validate({'foo': 'bar'})

        schema.structure.validate.assert_called_once_with({'foo': 'bar'})

    def test_it_raises_if_structure_validator_raises(self):
        request = testing.DummyRequest()
        schema = schemas.CreateAnnotationSchema(request)
        schema.structure = mock.Mock()
        schema.structure.validate.side_effect = schemas.ValidationError(
            'asplode')

        with pytest.raises(schemas.ValidationError):
            schema.validate({'foo': 'bar'})

    @pytest.mark.parametrize('field', [
        'created',
        'updated',
        'id',
    ])
    def test_it_removes_protected_fields(self, field):
        request = testing.DummyRequest()
        schema = schemas.CreateAnnotationSchema(request)
        data = {}
        data[field] = 'something forbidden'

        result = schema.validate(data)

        assert field not in result

    @pytest.mark.parametrize('data', [
        {},
        {'user': None},
        {'user': 'acct:foo@bar.com'},
    ])
    def test_it_ignores_input_user(self, data, authn_policy):
        """Any user field sent in the payload should be ignored."""
        authn_policy.authenticated_userid.return_value = (
            'acct:jeanie@example.com')
        request = testing.DummyRequest()
        schema = schemas.CreateAnnotationSchema(request)

        result = schema.validate(data)

        assert result == {'user': 'acct:jeanie@example.com'}

    @pytest.mark.parametrize('data,effective_principals,ok', [
        # No group supplied
        ({}, [], True),

        # World group
        ({'group': '__world__'}, [], False),
        ({'group': '__world__'}, [security.Everyone], True),

        # Other group
        ({'group': 'abcdef'}, [], False),
        ({'group': 'abcdef'}, [security.Everyone], False),
        ({'group': 'abcdef'}, [security.Everyone, 'group:abcdef'], True),
    ])
    def test_it_rejects_annotations_to_other_groups(self,
                                                    data,
                                                    effective_principals,
                                                    ok,
                                                    authn_policy):
        """
        A user cannot create an annotation in a group they're not a member of.

        If a group is specified in the annotation, then reject the creation if
        the relevant group principal is not present in the request's effective
        principals.
        """
        authn_policy.effective_principals.return_value = effective_principals
        request = testing.DummyRequest()
        schema = schemas.CreateAnnotationSchema(request)

        if ok:
            result = schema.validate(data)
            assert result.get('group') == data.get('group')

        else:
            with pytest.raises(schemas.ValidationError) as exc:
                schema.validate(data)
            assert exc.value.message.startswith('group:')

    @pytest.mark.parametrize('data', [
        {},
        {'foo': 'bar'},
        {'a_list': ['of', 'important', 'things']},
        {'an_object': {'with': 'stuff'}},
        {'numbers': 12345},
        {'null': None},
    ])
    def test_it_permits_all_other_changes(self, data):
        request = testing.DummyRequest()
        schema = schemas.CreateAnnotationSchema(request)

        result = schema.validate(data)

        for k in data:
            assert result[k] == data[k]


class TestUpdateAnnotationSchema(object):

    def test_it_passes_input_to_structure_validator(self):
        request = testing.DummyRequest()
        schema = schemas.UpdateAnnotationSchema(request, {})
        schema.structure = mock.Mock()
        schema.structure.validate.return_value = {}

        schema.validate({'foo': 'bar'})

        schema.structure.validate.assert_called_once_with({'foo': 'bar'})

    def test_it_raises_if_structure_validator_raises(self):
        request = testing.DummyRequest()
        schema = schemas.UpdateAnnotationSchema(request, {})
        schema.structure = mock.Mock()
        schema.structure.validate.side_effect = (
            schemas.ValidationError('asplode'))

        with pytest.raises(schemas.ValidationError):
            schema.validate({'foo': 'bar'})

    @pytest.mark.parametrize('field', [
        'created',
        'updated',
        'user',
        'id',
    ])
    def test_it_removes_protected_fields(self, field):
        request = testing.DummyRequest()
        annotation = {}
        schema = schemas.UpdateAnnotationSchema(request, annotation)
        data = {}
        data[field] = 'something forbidden'

        result = schema.validate(data)

        assert field not in result

    def test_it_allows_permissions_changes_if_admin(self, authn_policy):
        """If a user is an admin on an annotation, they can change perms."""
        authn_policy.authenticated_userid.return_value = (
            'acct:harriet@example.com')
        request = testing.DummyRequest()
        annotation = {
            'permissions': {'admin': ['acct:harriet@example.com']}
        }
        schema = schemas.UpdateAnnotationSchema(request, annotation)
        data = {
            'permissions': {'admin': ['acct:foo@example.com']}
        }

        result = schema.validate(data)

        assert result == data

    @pytest.mark.parametrize('annotation', [
        {},
        {'permissions': {}},
        {'permissions': {'admin': []}},
        {'permissions': {'admin': ['acct:alice@example.com']}},
        {'permissions': {'read': ['acct:mallory@example.com']}},
    ])
    def test_it_denies_permissions_changes_if_not_admin(self,
                                                        annotation,
                                                        authn_policy):
        """If a user isn't admin on an annotation they can't change perms."""
        authn_policy.authenticated_userid.return_value = (
            'acct:mallory@example.com')
        request = testing.DummyRequest()
        schema = schemas.UpdateAnnotationSchema(request, annotation)
        data = {
            'permissions': {'admin': ['acct:mallory@example.com']}
        }

        with pytest.raises(schemas.ValidationError) as exc:
            schema.validate(data)

        assert exc.value.message.startswith('permissions:')

    def test_it_denies_group_changes(self):
        """An annotation may not be moved between groups."""
        request = testing.DummyRequest()
        annotation = {'group': 'flibble'}
        schema = schemas.UpdateAnnotationSchema(request, annotation)
        data = {
            'group': '__world__'
        }

        with pytest.raises(schemas.ValidationError) as exc:
            schema.validate(data)

        assert exc.value.message.startswith('group:')

    @pytest.mark.parametrize('data', [
        {},
        {'foo': 'bar'},
        {'a_list': ['of', 'important', 'things']},
        {'an_object': {'with': 'stuff'}},
        {'numbers': 12345},
        {'null': None},
    ])
    def test_it_permits_all_other_changes(self, data):
        request = testing.DummyRequest()
        annotation = {'group': 'flibble'}
        schema = schemas.UpdateAnnotationSchema(request, annotation)

        result = schema.validate(data)

        for k in data:
            assert result[k] == data[k]
