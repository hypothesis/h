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


class TestAnnotationSchema(object):

    def test_it_does_not_raise_for_minimal_valid_data(self):
        schema = schemas.AnnotationSchema()

        # Use only the required fields.
        schema.validate(self.valid_input_data())

    def test_it_does_not_raise_for_full_valid_data(self):
        schema = schemas.AnnotationSchema()

        # Use all the keys to make sure that valid data for all of them passes.
        schema.validate({
            'document': {
                'dc': {
                    'identifier': ['foo', 'bar']
                },
                'highwire': {
                    'doi': ['foo', 'bar']
                },
                'link': [
                    {
                        'href': 'foo',
                        'type': 'foo',
                    },
                    {
                        'href': 'foo',
                        'type': 'foo',
                    }
                ],
            },
            'group': 'foo',
            'permissions': {
                'admin': ['acct:foo', 'group:bar'],
                'delete': ['acct:foo', 'group:bar'],
                'read': ['acct:foo', 'group:bar'],
                'update': ['acct:foo', 'group:bar'],
            },
            'references': ['foo', 'bar'],
            'tags': ['foo', 'bar'],
            'target': [
                {
                    'selector': 'foo'
                },
                {
                    'selector': 'foo'
                },
            ],
            'text': 'foo',
            'uri': 'foo',
        })

    @pytest.mark.parametrize("input_data,error_message", [
        ({'document': False}, "document: False is not of type 'object'"),

        ({'document': {'dc': False}},
         "document.dc: False is not of type 'object'"),

        ({'document': {'dc': {'identifier': False}}},
         "document.dc.identifier: False is not of type 'array'"),

        ({'document': {'dc': {'identifier': [False]}}},
         "document.dc.identifier.0: False is not of type 'string'"),

        ({'document': {'highwire': False}},
         "document.highwire: False is not of type 'object'"),

        ({'document': {'highwire': {'doi': False}}},
         "document.highwire.doi: False is not of type 'array'"),

        ({'document': {'highwire': {'doi': [False]}}},
         "document.highwire.doi.0: False is not of type 'string'"),

        ({'document': {'link': False}},
         "document.link: False is not of type 'array'"),

        ({'document': {'link': [False]}},
         "document.link.0: False is not of type 'object'"),

        ({'document': {'link': [{}]}},
         "document.link.0: 'href' is a required property"),

        ({'document': {'link': [{'href': False}]}},
         "document.link.0.href: False is not of type 'string'"),

        ({'document': {
            'link': [
                {
                    'href': 'http://example.com',
                    'type': False
                }
            ]
        }}, "document.link.0.type: False is not of type 'string'"),

        ({'group': False}, "group: False is not of type 'string'"),

        ({'permissions': False}, "permissions: False is not of type 'object'"),

        ({'permissions': {}}, "permissions: 'read' is a required property"),

        ({'permissions': {'read': False}},
         "permissions.read: False is not of type 'array'"),

        ({'permissions': {'read': [False]}},
         "permissions.read.0: False is not of type 'string'"),

        ({'permissions': {'read': ["foo"]}},
         "permissions.read.0: u'foo' does not match '^(acct:|group:).+$'"),

        ({'references': False}, "references: False is not of type 'array'"),

        ({'references': [False]},
         "references.0: False is not of type 'string'"),

        ({'tags': False}, "tags: False is not of type 'array'"),

        ({'tags': [False]}, "tags.0: False is not of type 'string'"),

        ({'target': False}, "target: False is not of type 'array'"),

        ({'target': [False]}, "target.0: False is not of type 'object'"),

        ({'target': [{}]}, "target.0: 'selector' is a required property"),

        ({'text': False}, "text: False is not of type 'string'"),

        ({'uri': False}, "uri: False is not of type 'string'"),
    ])
    def test_it_raises_for_invalid_data(self, input_data, error_message):
        schema = schemas.AnnotationSchema()

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(**input_data))

        assert str(err.value) == error_message

    @pytest.mark.parametrize('field', [
        'created',
        'updated',
        'user',
        'id',
        'links',
    ])
    def test_it_removes_protected_fields(self, field):
        schema = schemas.AnnotationSchema()

        appstruct = schema.validate(
            self.valid_input_data(field='something forbidden'))

        assert field not in appstruct

    def valid_input_data(self, **kwargs):
        """Return a minimal valid input data for AnnotationSchema."""
        data = {
            'permissions': {
                'read': [],
            },
        }
        data.update(kwargs)
        return data


class TestLegacyCreateAnnotationSchema(object):

    def test_it_passes_input_to_structure_validator(self, mock_request):
        schema = schemas.LegacyCreateAnnotationSchema(mock_request)
        schema.structure = mock.Mock()
        schema.structure.validate.return_value = {}

        schema.validate({'foo': 'bar'})

        schema.structure.validate.assert_called_once_with({'foo': 'bar'})

    def test_it_raises_if_structure_validator_raises(self, mock_request):
        schema = schemas.LegacyCreateAnnotationSchema(mock_request)
        schema.structure = mock.Mock()
        schema.structure.validate.side_effect = (
            schemas.ValidationError('asplode'))

        with pytest.raises(schemas.ValidationError):
            schema.validate({'foo': 'bar'})

    @pytest.mark.parametrize('field', [
        'created',
        'updated',
        'id',
        'links',
    ])
    def test_it_removes_protected_fields(self, field, mock_request):
        schema = schemas.LegacyCreateAnnotationSchema(mock_request)
        data = {}
        data[field] = 'something forbidden'

        appstruct = schema.validate(data)

        assert field not in appstruct

    @pytest.mark.parametrize('data', [
        {},
        {'user': None},
        {'user': 'acct:foo@bar.com'},
    ])
    def test_it_ignores_input_user(self, data, authn_policy, mock_request):
        """Any user field sent in the payload should be ignored."""
        authn_policy.authenticated_userid.return_value = (
            'acct:jeanie@example.com')
        schema = schemas.LegacyCreateAnnotationSchema(mock_request)

        appstruct = schema.validate(data)

        assert appstruct['user'] == 'acct:jeanie@example.com'

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
                                                    authn_policy,
                                                    mock_request):
        """
        A user cannot create an annotation in a group they're not a member of.

        If a group is specified in the annotation, then reject the creation if
        the relevant group principal is not present in the request's effective
        principals.
        """
        authn_policy.effective_principals.return_value = effective_principals
        schema = schemas.LegacyCreateAnnotationSchema(mock_request)

        if ok:
            appstruct = schema.validate(data)
            assert appstruct.get('group') == data.get('group')

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
    def test_it_permits_all_other_changes(self, data, mock_request):
        schema = schemas.LegacyCreateAnnotationSchema(mock_request)

        appstruct = schema.validate(data)

        for k in data:
            assert appstruct[k] == data[k]

    @pytest.fixture
    def mock_request(self):
        request = testing.DummyRequest()
        request.feature = mock.Mock(return_value=False,
                                    spec=lambda flag: False)
        return request


@pytest.mark.usefixtures('AnnotationSchema')
class TestCreateAnnotationSchema(object):

    def test_it_passes_input_to_AnnotationSchema_validator(self):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        schema.validate(mock.sentinel.input_data)

        schema.structure.validate.assert_called_once_with(
            mock.sentinel.input_data)

    def test_it_raises_if_AnnotationSchema_validate_raises(self,
                                                           AnnotationSchema):
        AnnotationSchema.return_value.validate.side_effect = (
            schemas.ValidationError('asplode'))
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError):
            schema.validate({'foo': 'bar'})

    def test_it_sets_userid(self, authn_policy):
        authn_policy.authenticated_userid.return_value = (
            'acct:harriet@example.com')
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate({})

        assert appstruct['userid'] == 'acct:harriet@example.com'

    def test_it_renames_uri_to_target_uri(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['uri'] = (
            'http://example.com/example')

        appstruct = schema.validate({})

        assert appstruct['target_uri'] == 'http://example.com/example'
        assert 'uri' not in appstruct

    def test_it_inserts_empty_string_if_data_has_no_uri(self,
                                                        AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        assert 'uri' not in AnnotationSchema.return_value.validate.return_value

        assert schema.validate({})['target_uri'] == ''

    def test_it_keeps_text(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['text'] = (
            'some annotation text')

        appstruct = schema.validate({})

        assert appstruct['text'] == 'some annotation text'

    def test_it_inserts_empty_string_if_data_contains_no_text(
            self,
            AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        assert 'text' not in AnnotationSchema.return_value.validate.return_value

        assert schema.validate({})['text'] == ''

    def test_it_keeps_tags(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['tags'] = [
            'foo', 'bar']

        appstruct = schema.validate({})

        assert appstruct['tags'] == ['foo', 'bar']

    def test_it_inserts_empty_list_if_data_contains_no_tags(self,
                                                            AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        assert 'tags' not in AnnotationSchema.return_value.validate.return_value

        assert schema.validate({})['tags'] == []

    def test_it_replaces_private_permissions_with_shared_False(
            self,
            AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['permissions'] = {
            'read': ['acct:harriet@example.com'],
        }
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate({})

        assert appstruct['shared'] is False
        assert 'permissions' not in appstruct

    def test_it_replaces_shared_permissions_with_shared_True(self,
                                                             AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['permissions'] = {
            'read': ['group:__world__'],
        }
        AnnotationSchema.return_value.validate.return_value['group'] = (
            '__world__')
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate({})

        assert appstruct['shared'] is True
        assert 'permissions' not in appstruct

    def test_it_defaults_to_private_if_no_permissions_object_sent(
            self,
            AnnotationSchema):
        del AnnotationSchema.return_value.validate.return_value['permissions']
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate({})

        assert appstruct['shared'] is False

    def test_it_does_not_crash_if_data_contains_no_target(self,
                                                          AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        assert 'target' not in AnnotationSchema.return_value.validate.return_value

        schema.validate({})

    def test_it_replaces_target_with_target_selectors(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['target'] = [
            {
                'foo': 'bar',  # This should be removed,
                'selector': 'the selectors',
            },
            'this should be removed',
        ]

        appstruct = schema.validate({})

        assert appstruct['target_selectors'] == 'the selectors'

    def test_it_renames_group_to_groupid(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['group'] = 'foo'

        appstruct = schema.validate({})

        assert appstruct['groupid'] == 'foo'
        assert 'group' not in appstruct

    def test_it_inserts_default_groupid_if_no_group(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        del AnnotationSchema.return_value.validate.return_value['group']

        appstruct = schema.validate({})

        assert appstruct['groupid'] == '__world__'

    def test_it_keeps_references(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['references'] = [
            'parent id', 'parent id 2']

        appstruct = schema.validate({})

        assert appstruct['references'] == ['parent id', 'parent id 2']

    def test_it_inserts_empty_list_if_no_references(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        assert 'references' not in AnnotationSchema.return_value.validate\
            .return_value

        appstruct = schema.validate({})

        assert appstruct['references'] == []

    def test_it_deletes_groupid_for_replies(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['group'] = 'foo'
        AnnotationSchema.return_value.validate.return_value['references'] = [
            'parent annotation id']

        appstruct = schema.validate({})

        assert 'groupid' not in appstruct

    def test_it_moves_extra_data_into_extra_sub_dict(self, AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value = {
            # Throw in all the fields, just to make sure that none of them get
            # into extra.
            'created': 'created',
            'updated': 'updated',
            'user': 'user',
            'id': 'id',
            'uri': 'uri',
            'text': 'text',
            'tags': ['gar', 'har'],
            'permissions': {'read': ['group:__world__']},
            'target': [],
            'group': '__world__',
            'references': ['parent'],

            # These should end up in extra.
            'foo': 1,
            'bar': 2,
        }

        appstruct = schema.validate({})

        assert appstruct['extra'] == {'foo': 1, 'bar': 2}

    def test_it_extracts_document_uris_from_the_document(
            self,
            AnnotationSchema,
            parse_document_claims):
        document_data = {'foo': 'bar'}
        target_uri = 'http://example.com/example'
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document_data)
        AnnotationSchema.return_value.validate.return_value['uri'] = target_uri
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        schema.validate({})

        parse_document_claims.document_uris_from_data.assert_called_once_with(
            document_data,
            claimant=target_uri,
        )

    def test_it_puts_document_uris_in_appstruct(self, parse_document_claims):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate({})

        assert appstruct['document']['document_uri_dicts'] == (
            parse_document_claims.document_uris_from_data.return_value)

    def test_it_extracts_document_metas_from_the_document(
            self,
            AnnotationSchema,
            parse_document_claims):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        document_data = {'foo': 'bar'}
        target_uri = 'http://example.com/example'
        AnnotationSchema.return_value.validate.return_value['document'] = {
            'foo': 'bar'}
        AnnotationSchema.return_value.validate.return_value['uri'] = target_uri

        schema.validate({})

        parse_document_claims.document_metas_from_data.assert_called_once_with(
            document_data,
            claimant=target_uri,
        )

    def test_it_does_not_pass_modified_dict_to_document_metas_from_data(
            self,
            AnnotationSchema,
            parse_document_claims):
        """

        If document_uris_from_data() modifies the document dict that it's
        given, the original dict (or one with the same values as it) should be
        passed t document_metas_from_data(), not the modified copy.

        """
        document = {
            'top_level_key': 'original_value',
            'sub_dict': {
                'key': 'original_value'
            }
        }

        def document_uris_from_data(document, claimant):
            document['new_key'] = 'new_value'
            document['top_level_key'] = 'new_value'
            document['sub_dict']['key'] = 'new_value'
        parse_document_claims.document_uris_from_data.side_effect = (
            document_uris_from_data)
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document)

        schema.validate({})

        assert (
            parse_document_claims.document_metas_from_data.call_args[0][0] ==
            document)

    def test_it_puts_document_metas_in_appstruct(self, parse_document_claims):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate({})

        assert appstruct['document']['document_meta_dicts'] == (
            parse_document_claims.document_metas_from_data.return_value)

    def test_it_clears_existing_keys_from_document(self, AnnotationSchema):
        """
        Any keys in the document dict should be removed.

        They're replaced with the 'document_uri_dicts' and
        'document_meta_dicts' keys.

        """
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())
        AnnotationSchema.return_value.validate.return_value['document'] = {
            'foo': 'bar'  # This should be deleted.
        }

        appstruct = schema.validate({})

        assert 'foo' not in appstruct['document']


class TestLegacyUpdateAnnotationSchema(object):

    def test_it_passes_input_to_structure_validator(self):
        request = testing.DummyRequest()
        schema = schemas.LegacyUpdateAnnotationSchema(request, {})
        schema.structure = mock.Mock()
        schema.structure.validate.return_value = {}

        schema.validate({'foo': 'bar'})

        schema.structure.validate.assert_called_once_with({'foo': 'bar'})

    def test_it_raises_if_structure_validator_raises(self):
        request = testing.DummyRequest()
        schema = schemas.LegacyUpdateAnnotationSchema(request, {})
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
        'links',
    ])
    def test_it_removes_protected_fields(self, field):
        request = testing.DummyRequest()
        annotation = {}
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)
        data = {}
        data[field] = 'something forbidden'

        appstruct = schema.validate(data)

        assert field not in appstruct

    def test_it_allows_permissions_changes_if_admin(self, authn_policy):
        """If a user is an admin on an annotation, they can change perms."""
        authn_policy.authenticated_userid.return_value = (
            'acct:harriet@example.com')
        request = testing.DummyRequest()
        annotation = {
            'permissions': {'admin': ['acct:harriet@example.com']}
        }
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)
        data = {
            'permissions': {'admin': ['acct:foo@example.com']}
        }

        appstruct = schema.validate(data)

        assert appstruct == data

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
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)
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
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)
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
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)

        appstruct = schema.validate(data)

        for k in data:
            assert appstruct[k] == data[k]


@pytest.mark.usefixtures('AnnotationSchema')
class TestUpdateAnnotationSchema(object):

    def test_it_passes_input_to_AnnotationSchema_validate(self):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        schema.validate(mock.sentinel.input_data)

        schema.structure.validate.assert_called_once_with(
            mock.sentinel.input_data)

    def test_it_raises_if_AnnotationSchema_validate_raises(self,
                                                           AnnotationSchema):
        AnnotationSchema.return_value.validate.side_effect = (
            schemas.ValidationError('asplode'))
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        with pytest.raises(schemas.ValidationError):
            schema.validate({})

    def test_you_cannot_update_protected_fields(self,
                                                AnnotationSchema):
        for protected_field in ['created', 'updated', 'user', 'id', 'links']:
            AnnotationSchema.return_value.validate\
                .return_value[protected_field] = 'foo'
            schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                    '',
                                                    '')

            appstruct = schema.validate({})

            assert protected_field not in appstruct
            assert protected_field not in appstruct.get('extra', {})

    def test_you_cannot_change_an_annotations_group(self,
                                                    AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['groupid'] = (
            'new-group')
        AnnotationSchema.return_value.validate.return_value['group'] = (
            'new-group')
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert 'groupid' not in appstruct
        assert 'groupid' not in appstruct.get('extra', {})
        assert 'group' not in appstruct
        assert 'group' not in appstruct.get('extra', {})

    def test_you_cannot_change_an_annotations_userid(self,
                                                     AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['userid'] = (
            'new_userid')
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert 'userid' not in appstruct
        assert 'userid' not in appstruct.get('extra', {})

    def test_you_cannot_change_an_annotations_references(self,
                                                         AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['references'] = [
            'new_parent']
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert 'references' not in appstruct
        assert 'references' not in appstruct.get('extra', {})

    def test_it_renames_uri_to_target_uri(self, AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['uri'] = (
            'http://example.com/example')

        appstruct = schema.validate({})

        assert appstruct['target_uri'] == 'http://example.com/example'
        assert 'uri' not in appstruct
        assert 'uri' not in appstruct.get('extras', {})

    def test_it_replaces_private_permissions_with_shared_False(
            self,
            AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['permissions'] = {
            'read': ['acct:harriet@example.com'],
        }
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert appstruct['shared'] is False
        assert 'permissions' not in appstruct
        assert 'permissions' not in appstruct.get('extras', {})

    def test_it_replaces_shared_permissions_with_shared_True(self,
                                                             AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['permissions'] = {
            'read': ['group:__world__'],
        }
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                '',
                                                '__world__')

        appstruct = schema.validate({})

        assert appstruct['shared'] is True
        assert 'permissions' not in appstruct
        assert 'permissions' not in appstruct.get('extras', {})

    def test_it_converts_target_to_target_selectors(self,
                                                    AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['target'] = [
            {
                'foo': 'bar',  # This should be removed,
                'selector': 'the selectors',
            },
            'this should be removed',
        ]

        appstruct = schema.validate({})

        assert appstruct['target_selectors'] == 'the selectors'
        assert 'target' not in appstruct
        assert 'target' not in appstruct.get('extras', {})

    def test_you_can_update_text(self, AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['text'] = 'new'

        appstruct = schema.validate({})

        assert appstruct['text'] == 'new'

    def test_you_can_update_tags(self, AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['tags'] = ['new']

        appstruct = schema.validate({})

        assert appstruct['tags'] == ['new']

    def test_it_extracts_document_uris_from_the_document(
            self,
            AnnotationSchema,
            parse_document_claims):
        document_data = {'foo': 'bar'}
        target_uri = 'http://example.com/example'
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document_data)
        AnnotationSchema.return_value.validate.return_value['uri'] = target_uri
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        schema.validate({})

        parse_document_claims.document_uris_from_data.assert_called_once_with(
            document_data,
            claimant=target_uri,
        )

    def test_it_passes_existing_target_uri_to_document_uris_from_data(
            self,
            AnnotationSchema,
            parse_document_claims):
        """
        If no 'uri' is given it should use the existing target_uri.

        If no 'uri' is given in the update request then
        document_uris_from_data() should be called with the existing
        target_uri of the annotation in the database.

        """
        document_data = {'foo': 'bar'}
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document_data)
        assert 'uri' not in AnnotationSchema.return_value.validate.return_value
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                mock.sentinel.target_uri,
                                                '')

        schema.validate({})

        parse_document_claims.document_uris_from_data.assert_called_once_with(
            document_data,
            claimant=mock.sentinel.target_uri)

    def test_it_puts_document_uris_in_appstruct(self,
                                                AnnotationSchema,
                                                parse_document_claims):
        AnnotationSchema.return_value.validate.return_value['document'] = {}
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert appstruct['document']['document_uri_dicts'] == (
            parse_document_claims.document_uris_from_data.return_value)

    def test_it_extracts_document_metas_from_the_document(
            self,
            AnnotationSchema,
            parse_document_claims):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        document_data = {'foo': 'bar'}
        target_uri = 'http://example.com/example'
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document_data)
        AnnotationSchema.return_value.validate.return_value['uri'] = target_uri

        schema.validate({})

        parse_document_claims.document_metas_from_data.assert_called_once_with(
            document_data,
            claimant=target_uri
        )

    def test_it_passes_existing_target_uri_to_document_metas_from_data(
            self,
            AnnotationSchema,
            parse_document_claims):
        """
        If no 'uri' is given it should use the existing target_uri.

        If no 'uri' is given in the update request then
        document_metas_from_data() should be called with the existing
        target_uri of the annotation in the database.

        """
        document_data = {'foo': 'bar'}
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document_data)
        assert 'uri' not in AnnotationSchema.return_value.validate.return_value
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                mock.sentinel.target_uri,
                                                '')

        schema.validate({})

        parse_document_claims.document_metas_from_data.assert_called_once_with(
            document_data,
            claimant=mock.sentinel.target_uri)

    def test_it_does_not_pass_modified_dict_to_document_metas_from_data(
            self,
            AnnotationSchema,
            parse_document_claims):
        """

        If document_uris_from_data() modifies the document dict that it's
        given, the original dict (or one with the same values as it) should be
        passed t document_metas_from_data(), not the modified copy.

        """
        document = {
            'top_level_key': 'original_value',
            'sub_dict': {
                'key': 'original_value'
            }
        }

        def document_uris_from_data(document, claimant):
            document['new_key'] = 'new_value'
            document['top_level_key'] = 'new_value'
            document['sub_dict']['key'] = 'new_value'
        parse_document_claims.document_uris_from_data.side_effect = (
            document_uris_from_data)
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['document'] = (
            document)

        schema.validate({})

        assert (
            parse_document_claims.document_metas_from_data.call_args[0][0] ==
            document)

    def test_it_puts_document_metas_in_appstruct(self,
                                                 AnnotationSchema,
                                                 parse_document_claims):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['document'] = {}

        appstruct = schema.validate({})

        assert appstruct['document']['document_meta_dicts'] == (
            parse_document_claims.document_metas_from_data.return_value)

    def test_it_clears_existing_keys_from_document(self,
                                                   AnnotationSchema):
        """
        Any keys in the document dict should be removed.

        They're replaced with the 'document_uri_dicts' and
        'document_meta_dicts' keys.

        """
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['document'] = {
            'foo': 'bar'  # This should be deleted.
        }

        appstruct = schema.validate({})

        assert 'foo' not in appstruct['document']

    def test_document_does_not_end_up_in_extra(self,
                                               AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        AnnotationSchema.return_value.validate.return_value['document'] = {
            'foo': 'bar'
        }

        appstruct = schema.validate({})

        assert 'document' not in appstruct.get('extra', {})

    def test_it_does_not_crash_when_fields_are_missing(self,
                                                       AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value = {}
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        schema.validate({})

    def test_it_adds_extra_fields_into_the_extra_dict(self,
                                                      AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['foo'] = 'bar'
        AnnotationSchema.return_value.validate.return_value['custom'] = 23
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert appstruct['extra'] == {'foo': 'bar', 'custom': 23}

    def test_it_overwrites_extra_fields_in_the_extra_dict(self,
                                                          AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['foo'] = 'bar'
        AnnotationSchema.return_value.validate.return_value['custom'] = 23
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert appstruct['extra'] == {'foo': 'bar', 'custom': 23}

    def test_it_does_not_modify_extra_fields_that_are_not_sent(
            self,
            AnnotationSchema):
        AnnotationSchema.return_value.validate.return_value['foo'] = 'bar'
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')

        appstruct = schema.validate({})

        assert 'custom' not in appstruct['extra']

    def test_it_does_not_modify_extra_fields_if_none_are_sent(
            self,
            AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(), '', '')
        assert 'extra' not in AnnotationSchema.return_value.validate\
            .return_value

        appstruct = schema.validate({})

        assert not appstruct.get('extra')


@pytest.fixture
def AnnotationSchema(patch):
    cls = patch('h.api.schemas.AnnotationSchema')
    cls.return_value.validate.return_value = {
        'permissions': {
            'read': ['group:__world__'],
            'update': ['acct:testuser@hypothes.is'],
            'delete': ['acct:testuser@hypothes.is'],
        },
        'group': '__world__',
    }
    return cls


@pytest.fixture
def parse_document_claims(patch):
    return patch('h.api.schemas.parse_document_claims')
