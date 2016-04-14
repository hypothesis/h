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
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        # Use only the required fields.
        schema.validate(self.valid_input_data())

    def test_it_does_not_raise_for_full_valid_data(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

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
            'uri' : 'foo',
        })

    def test_it_raises_if_document_is_not_a_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document=False,
            ))

        assert str(err.value) == "document: False is not of type 'object'"

    def test_it_raises_if_document_dc_is_not_a_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'dc': False}
            ))

        assert str(err.value) == "document.dc: False is not of type 'object'"

    def test_it_raises_if_document_dc_identifier_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'dc': {'identifier': False}}
            ))

        assert str(err.value) == (
            "document.dc.identifier: False is not of type 'array'")

    def test_it_raises_if_document_dc_identifier_item_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'dc': {'identifier': [False]}}
            ))

        assert str(err.value) == (
            "document.dc.identifier.0: False is not of type 'string'")

    def test_it_raises_if_document_highwire_is_not_a_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'highwire': False}
            ))

        assert str(err.value) == (
            "document.highwire: False is not of type 'object'")

    def test_it_raises_if_document_highwire_doi_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'highwire': {'doi': False}}
            ))

        assert str(err.value) == (
            "document.highwire.doi: False is not of type 'array'")

    def test_it_raises_if_document_highwire_doi_item_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'highwire': {'doi': [False]}}
            ))

        assert str(err.value) == (
            "document.highwire.doi.0: False is not of type 'string'")

    def test_it_raises_if_document_link_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'link': False}
            ))

        assert str(err.value) == "document.link: False is not of type 'array'"

    def test_it_raises_if_document_link_item_is_not_a_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'link': [False]}
            ))

        assert str(err.value) == (
            "document.link.0: False is not of type 'object'")

    def test_it_raises_if_document_link_item_has_no_href(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'link': [{}]}
            ))

        assert str(err.value) == (
            "document.link.0: 'href' is a required property")

    def test_it_raises_if_document_link_item_href_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={'link': [{'href': False}]}
            ))

        assert str(err.value) == (
            "document.link.0.href: False is not of type 'string'")

    def test_it_raises_if_document_link_item_type_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                document={
                    'link': [
                        {
                            'href': 'http://example.com',
                            'type': False
                        }
                    ]
                }
            ))

        assert str(err.value) == (
            "document.link.0.type: False is not of type 'string'")

    def test_it_raises_if_group_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                group=False
            ))

        assert str(err.value) == "group: False is not of type 'string'"

    def test_it_raises_if_permissions_is_missing(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())
        data = self.valid_input_data()
        del data['permissions']

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(data)

        assert str(err.value) == "'permissions' is a required property"

    def test_it_raises_if_permissions_is_not_a_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                permissions=False
            ))

        assert str(err.value) == "permissions: False is not of type 'object'"

    def test_it_raises_if_permissions_has_no_read(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                permissions={}
            ))

        assert str(err.value) == "permissions: 'read' is a required property"

    def test_it_raises_if_permissions_read_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                permissions={'read': False}
            ))

        assert str(err.value) == (
            "permissions.read: False is not of type 'array'")

    def test_it_raises_if_permissions_read_item_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                permissions={'read': [False]}
            ))

        assert str(err.value) == (
            "permissions.read.0: False is not of type 'string'")

    def test_it_raises_if_permissions_read_item_is_wrong_format(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                permissions={'read': ["foo"]}
            ))

        assert str(err.value) == (
            "permissions.read.0: u'foo' does not match '^(acct:|group:).+$'")

    def test_it_raises_if_references_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                references=False
            ))

        assert str(err.value) == "references: False is not of type 'array'"

    def test_it_raises_if_references_item_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                references=[False]
            ))

        assert str(err.value) == "references.0: False is not of type 'string'"

    def test_it_raises_if_tags_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                tags=False
            ))

        assert str(err.value) == "tags: False is not of type 'array'"

    def test_it_raises_if_tags_item_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                tags=[False]
            ))

        assert str(err.value) == "tags.0: False is not of type 'string'"

    def test_it_raises_if_target_is_not_a_list(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                target=False
            ))

        assert str(err.value) == "target: False is not of type 'array'"

    def test_it_raises_if_target_item_is_not_a_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                target=[False]
            ))

        assert str(err.value) == "target.0: False is not of type 'object'"

    def test_it_raises_if_target_has_no_selector(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                target=[{}]
            ))

        assert str(err.value) == "target.0: 'selector' is a required property"

    def test_it_raises_if_text_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                text=False
            ))

        assert str(err.value) == "text: False is not of type 'string'"

    def test_it_raises_if_uri_is_not_a_string(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        with pytest.raises(schemas.ValidationError) as err:
            schema.validate(self.valid_input_data(
                uri=False
            ))

        assert str(err.value) == "uri: False is not of type 'string'"

    def valid_input_data(self, **kwargs):
        """Return a minimal valid input data for AnnotationSchema."""
        data = {
            'permissions': {
                'read': [],
            },
        }
        data.update(kwargs)
        return data

    @pytest.mark.parametrize('field', [
        'created',
        'updated',
        'user',
        'id',
    ])
    def test_it_removes_protected_fields(self, field):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(annotation_data(field='something forbidden'))

        assert field not in result

    def test_it_sets_userid(self, authn_policy):
        authn_policy.authenticated_userid.return_value = (
            'acct:harriet@example.com')
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(annotation_data())

        assert result['userid'] == 'acct:harriet@example.com'

    def test_it_renames_uri_to_target_uri(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(
            annotation_data(uri='http://example.com/example'),
        )

        assert result['target_uri'] == 'http://example.com/example'
        assert 'uri' not in result

    def test_it_inserts_empty_string_if_data_has_no_uri(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        data = annotation_data()
        assert 'uri' not in data

        assert schema.validate(data)['target_uri'] == ''

    def test_it_keeps_text(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(annotation_data(text='some annotation text'))

        assert result['text'] == 'some annotation text'

    def test_it_inserts_empty_string_if_data_contains_no_text(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        data = annotation_data()
        assert 'text' not in data

        assert schema.validate(data)['text'] == ''

    def test_it_keeps_tags(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(annotation_data(tags=['foo', 'bar']))

        assert result['tags'] == ['foo', 'bar']

    def test_it_inserts_empty_list_if_data_contains_no_tags(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        data = annotation_data()
        assert 'tags' not in data

        assert schema.validate(data)['tags'] == []

    def test_it_replaces_private_permissions_with_shared_False(
            self,
            authn_policy):
        authn_policy.authenticated_userid.return_value = (
            'acct:harriet@example.com')
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(
            annotation_data(
                permissions={'read': ['acct:harriet@example.com']},
            ),
        )

        assert result['shared'] is False
        assert 'permissions' not in result

    def test_it_replaces_shared_permissions_with_shared_True(
            self,
            authn_policy):
        authn_policy.authenticated_userid.return_value = (
            'acct:harriet@example.com')
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(
            annotation_data(
                permissions={'read': ['group:__world__']},
            ),
        )

        assert result['shared'] is True
        assert 'permissions' not in result

    def test_it_does_not_crash_if_data_contains_no_target(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        data = annotation_data()
        assert 'target' not in data

        schema.validate(data)

    def test_it_replaces_target_with_target_selectors(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(
            annotation_data(
                target=[
                    {
                        'foo': 'bar',  # This should be removed,
                        'selector': 'the selectors',
                    },
                    'this should be removed',
                ],
            ),
        )

        assert result['target_selectors'] == 'the selectors'

    def test_it_renames_group_to_groupid(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(annotation_data(group='foo'))

        assert result['groupid'] == 'foo'
        assert 'group' not in result

    def test_it_inserts_default_groupid_if_no_group(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        data = annotation_data()
        assert 'group' not in data

        result = schema.validate(data)

        assert result['groupid'] == '__world__'

    def test_it_keeps_references(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(
            annotation_data(references=['parent id', 'parent id 2']))

        assert result['references'] == ['parent id', 'parent id 2']

    def test_it_inserts_empty_list_if_no_references(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        data = annotation_data()
        assert 'references' not in data

        result = schema.validate(data)

        assert result['references'] == []

    def test_it_deletes_groupid_for_replies(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate(
            annotation_data(
                group='foo',
                references=['parent annotation id'],
            )
        )

        assert 'groupid' not in result

    def test_it_moves_extra_data_into_extra_sub_dict(self):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        result = schema.validate({
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
        })

        assert result['extra'] == {'foo': 1, 'bar': 2}

    def test_it_calls_document_uris_from_data(self, parse_document_claims):
        document_data = {'foo': 'bar'}
        target_uri = 'http://example.com/example'
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        schema.validate(
            annotation_data(
                document=document_data,
                uri=target_uri,
            )
        )

        parse_document_claims.document_uris_from_data.assert_called_once_with(
            document_data,
            claimant=target_uri,
        )

    def test_it_puts_document_uris_in_appstruct(self, parse_document_claims):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate(annotation_data())

        assert appstruct['document']['document_uri_dicts'] == (
            parse_document_claims.document_uris_from_data.return_value)

    def test_it_calls_document_metas_from_data(self, parse_document_claims):
        schema = schemas.AnnotationSchema(testing.DummyRequest())
        document_data = {'foo': 'bar'}
        target_uri = 'http://example.com/example'

        schema.validate(
            annotation_data(
                document=document_data,
                uri=target_uri,
            )
        )

        parse_document_claims.document_metas_from_data.assert_called_once_with(
            document_data,
            claimant=target_uri,
        )

    def test_it_does_not_pass_modified_dict_to_document_metas_from_data(
            self,
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
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        schema.validate(annotation_data(document=document))

        assert (
            parse_document_claims.document_metas_from_data.call_args[0][0] ==
            document)

    def test_it_puts_document_metas_in_appstruct(self, parse_document_claims):
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate(annotation_data())

        assert appstruct['document']['document_meta_dicts'] == (
            parse_document_claims.document_metas_from_data.return_value)

    def test_it_clears_existing_keys_from_document(self):
        """
        Any keys in the document dict should be removed.

        They're replaced with the 'document_uri_dicts' and
        'document_meta_dicts' keys.

        """
        schema = schemas.AnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate(
            annotation_data(
                document={
                    'foo': 'bar'  # This should be deleted.
                },
            ),
        )

        assert 'foo' not in appstruct['document']

    @pytest.fixture
    def parse_document_claims(self, patch):
        return patch('h.api.schemas.parse_document_claims')


class TestLegacyCreateAnnotationSchema(object):

    def test_it_passes_input_to_structure_validator(self):
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema(request)
        schema.structure = mock.Mock()
        schema.structure.validate.return_value = {}

        schema.validate({'foo': 'bar'})

        schema.structure.validate.assert_called_once_with({'foo': 'bar'})

    def test_it_raises_if_structure_validator_raises(self):
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema(request)
        schema.structure = mock.Mock()
        schema.structure.validate.side_effect = (
            schemas.ValidationError('asplode'))

        with pytest.raises(schemas.ValidationError):
            schema.validate({'foo': 'bar'})

    @pytest.mark.parametrize('field', [
        'created',
        'updated',
        'id',
    ])
    def test_it_removes_protected_fields(self, field):
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema(request)
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
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema(request)

        result = schema.validate(data)

        assert result['user'] == 'acct:jeanie@example.com'

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
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema(request)

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
        request = self.mock_request()
        schema = schemas.LegacyCreateAnnotationSchema(request)

        result = schema.validate(data)

        for k in data:
            assert result[k] == data[k]

    def mock_request(self):
        request = testing.DummyRequest()
        request.feature = mock.Mock(return_value=False,
                                    spec=lambda flag: False)
        return request


@pytest.mark.usefixtures('AnnotationSchema')
class TestCreateAnnotationSchema(object):

    def test_it_passes_input_to_AnnotationSchema_validator(self,
                                                           AnnotationSchema):
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

    def test_it_returns_the_appstruct_from_AnnotationSchema(self,
                                                            AnnotationSchema):
        schema = schemas.CreateAnnotationSchema(testing.DummyRequest())

        appstruct = schema.validate(mock.sentinel.input_data)

        assert appstruct == AnnotationSchema.return_value.validate.return_value


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
    ])
    def test_it_removes_protected_fields(self, field):
        request = testing.DummyRequest()
        annotation = {}
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)
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
        schema = schemas.LegacyUpdateAnnotationSchema(request, annotation)
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

        result = schema.validate(data)

        for k in data:
            assert result[k] == data[k]


@pytest.mark.usefixtures('AnnotationSchema')
class TestUpdateAnnotationSchema(object):

    def test_it_passes_input_to_AnnotationSchema_validator(self,
                                                           annotation,
                                                           AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                annotation)

        schema.validate(mock.sentinel.input_data)

        schema.structure.validate.assert_called_once_with(
            mock.sentinel.input_data)

    def test_it_raises_if_AnnotationSchema_validate_raises(self,
                                                           annotation,
                                                           AnnotationSchema):
        AnnotationSchema.return_value.validate.side_effect = (
            schemas.ValidationError('asplode'))
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                annotation)

        with pytest.raises(schemas.ValidationError):
            schema.validate({'foo': 'bar'})

    def test_it_raises_if_you_try_to_change_the_group(self,
                                                      annotation,
                                                      AnnotationSchema):
        annotation.groupid = 'original-group'
        AnnotationSchema.return_value.validate.return_value['groupid'] = (
            'new-group')
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                annotation)

        with pytest.raises(schemas.ValidationError):
            schema.validate(mock.sentinel.input_data)

    def test_it_returns_the_appstruct_from_AnnotationSchema(self,
                                                            annotation,
                                                            AnnotationSchema):
        schema = schemas.UpdateAnnotationSchema(testing.DummyRequest(),
                                                annotation)

        appstruct = schema.validate(mock.sentinel.input_data)

        assert appstruct == AnnotationSchema.return_value.validate.return_value


    @pytest.fixture
    def annotation(self):
        return mock.Mock(groupid='foogroup')

def annotation_data(**kwargs):
    """Return test input data for AnnotationSchema.validate()."""
    data = {
        'permissions': {
            'read': []
        }
    }
    data.update(kwargs)
    return data


@pytest.fixture
def AnnotationSchema(patch):
    cls = patch('h.api.schemas.AnnotationSchema')
    cls.return_value.validate.return_value = {
        'groupid': 'foogroup',
    }
    return cls
