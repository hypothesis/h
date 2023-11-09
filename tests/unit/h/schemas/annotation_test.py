from copy import deepcopy
from unittest import mock

import pytest
from webob.multidict import MultiDict, NestedMultiDict

from h.schemas import ValidationError
from h.schemas.annotation import (
    CreateAnnotationSchema,
    SearchParamsSchema,
    UpdateAnnotationSchema,
    URLMigrationSchema,
)
from h.schemas.util import validate_query_params
from h.search.query import LIMIT_DEFAULT, LIMIT_MAX, OFFSET_MAX


def create_annotation_schema_validate(request, data):
    # 'uri' is required when creating new annotations.
    if "uri" not in data:
        data["uri"] = "http://example.com/example"

    schema = CreateAnnotationSchema(request)
    return schema.validate(data)


def update_annotation_schema_validate(
    request, data, existing_target_uri="", groupid=""
):
    schema = UpdateAnnotationSchema(request, existing_target_uri, groupid)
    return schema.validate(data)


@pytest.mark.parametrize(
    "validate",
    [create_annotation_schema_validate, update_annotation_schema_validate],
    ids=["CreateAnnotationSchema.validate()", "UpdateAnnotationSchema.validate()"],
)
class TestCreateUpdateAnnotationSchema:
    """Shared tests for CreateAnnotationSchema and UpdateAnnotationSchema."""

    def test_it_does_not_raise_for_minimal_valid_data(self, pyramid_request, validate):
        validate(pyramid_request, {})

    def test_it_does_not_raise_for_full_valid_data(self, pyramid_request, validate):
        # Use all the keys to make sure that valid data for all of them passes.
        validate(
            pyramid_request,
            {
                "document": {
                    "dc": {"identifier": ["foo", "bar"]},
                    "highwire": {"doi": ["foo", "bar"], "pdf_url": ["foo", "bar"]},
                    "link": [
                        {"href": "foo", "type": "foo"},
                        {"href": "foo", "type": "foo"},
                    ],
                },
                "group": "foo",
                "permissions": {
                    "admin": ["acct:foo", "group:bar"],
                    "delete": ["acct:foo", "group:bar"],
                    "read": ["acct:foo", "group:bar"],
                    "update": ["acct:foo", "group:bar"],
                },
                "references": ["foo", "bar"],
                "tags": ["foo", "bar"],
                "target": [
                    {"selector": [{"type": "foo"}]},
                    {"selector": [{"type": "bar"}]},
                ],
                "text": "foo",
                "uri": "foo",
            },
        )

    @pytest.mark.parametrize(
        "input_data,error_message",
        [
            ({"document": False}, "document: False is not of type 'object'"),
            ({"document": {"dc": False}}, "document.dc: False is not of type 'object'"),
            (
                {"document": {"dc": {"identifier": False}}},
                "document.dc.identifier: False is not of type 'array'",
            ),
            (
                {"document": {"dc": {"identifier": [False]}}},
                "document.dc.identifier.0: False is not of type 'string'",
            ),
            (
                {"document": {"highwire": False}},
                "document.highwire: False is not of type 'object'",
            ),
            (
                {"document": {"highwire": {"doi": False}}},
                "document.highwire.doi: False is not of type 'array'",
            ),
            (
                {"document": {"highwire": {"doi": [False]}}},
                "document.highwire.doi.0: False is not of type 'string'",
            ),
            (
                {"document": {"highwire": {"pdf_url": False}}},
                "document.highwire.pdf_url: False is not of type 'array'",
            ),
            (
                {"document": {"highwire": {"pdf_url": [False]}}},
                "document.highwire.pdf_url.0: False is not of type 'string'",
            ),
            (
                {"document": {"link": False}},
                "document.link: False is not of type 'array'",
            ),
            (
                {"document": {"link": [False]}},
                "document.link.0: False is not of type 'object'",
            ),
            (
                {"document": {"link": [{}]}},
                "document.link.0: 'href' is a required property",
            ),
            (
                {"document": {"link": [{"href": False}]}},
                "document.link.0.href: False is not of type 'string'",
            ),
            (
                {"document": {"link": [{"href": "http://example.com", "type": False}]}},
                "document.link.0.type: False is not of type 'string'",
            ),
            ({"group": False}, "group: False is not of type 'string'"),
            ({"permissions": False}, "permissions: False is not of type 'object'"),
            ({"permissions": {}}, "permissions: 'read' is a required property"),
            (
                {"permissions": {"read": False}},
                "permissions.read: False is not of type 'array'",
            ),
            (
                {"permissions": {"read": [False]}},
                "permissions.read.0: False is not of type 'string'",
            ),
            (
                {"permissions": {"read": ["foo"]}},
                "permissions.read.0: 'foo' does not match '^(acct:|group:).+$'",
            ),
            ({"references": False}, "references: False is not of type 'array'"),
            ({"references": [False]}, "references.0: False is not of type 'string'"),
            ({"tags": False}, "tags: False is not of type 'array'"),
            ({"tags": [False]}, "tags.0: False is not of type 'string'"),
            ({"target": False}, "target: False is not of type 'array'"),
            ({"target": [False]}, "target.0: False is not of type 'object'"),
            (
                {"target": [{"selector": False}]},
                "target.0.selector: False is not of type 'array'",
            ),
            (
                {"target": [{"selector": {"type": "foo"}}]},
                "target.0.selector: {'type': 'foo'} is not of type 'array'",
            ),
            (
                {"target": [{"selector": [False]}]},
                "target.0.selector.0: False is not of type 'object'",
            ),
            (
                {"target": [{"selector": [{}]}]},
                "target.0.selector.0: 'type' is a required property",
            ),
            (
                {"target": [{"selector": [{"type": False}]}]},
                "target.0.selector.0.type: False is not of type 'string'",
            ),
            ({"text": False}, "text: False is not of type 'string'"),
            ({"uri": False}, "uri: False is not of type 'string'"),
            ({"uri": ""}, "uri: 'uri' is a required property"),
            ({"uri": " "}, "uri: 'uri' is a required property"),
        ],
    )
    def test_it_raises_for_invalid_data(
        self, pyramid_request, validate, input_data, error_message
    ):
        with pytest.raises(ValidationError) as exc:
            validate(pyramid_request, input_data)

        actual_msg = str(exc.value)
        assert actual_msg == error_message

    @pytest.mark.parametrize(
        "field",
        [
            "created",
            "updated",
            "user",
            "id",
            "links",
            "flagged",
            "hidden",
            "moderation",
            "user_info",
        ],
    )
    def test_it_removes_protected_fields(self, pyramid_request, validate, field):
        data = {}
        data[field] = "something forbidden"
        appstruct = validate(pyramid_request, data)

        assert field not in appstruct
        assert field not in appstruct.get("extra", {})

    def test_it_renames_uri_to_target_uri(self, pyramid_request, validate):
        appstruct = validate(pyramid_request, {"uri": "http://example.com/example"})

        assert appstruct["target_uri"] == "http://example.com/example"
        assert "uri" not in appstruct

    def test_it_strips_leading_and_trailing_whitespace_from_uri(
        self, pyramid_request, validate
    ):
        appstruct = validate(pyramid_request, {"uri": " foo "})

        assert appstruct["target_uri"] == "foo"

    def test_it_keeps_text(self, pyramid_request, validate):
        appstruct = validate(pyramid_request, {"text": "some annotation text"})

        assert appstruct["text"] == "some annotation text"

    def test_it_keeps_tags(self, pyramid_request, validate):
        appstruct = validate(pyramid_request, {"tags": ["foo", "bar"]})

        assert appstruct["tags"] == ["foo", "bar"]

    def test_it_replaces_target_with_target_selectors(self, pyramid_request, validate):
        appstruct = validate(
            pyramid_request,
            {
                "target": [
                    {
                        "foo": "bar",  # This should be removed
                        "selector": [{"type": "FooSelector"}, {"type": "BarSelector"}],
                    },
                    {
                        # Additional targets are ignored.
                        "selector": [{"type": "BazSelector"}]
                    },
                ]
            },
        )

        assert appstruct["target_selectors"] == [
            {"type": "FooSelector"},
            {"type": "BarSelector"},
        ]

    def test_it_extracts_document_uris_from_the_document(
        self, pyramid_request, document_claims, validate
    ):
        target_uri = "http://example.com/example"
        document_data = {"foo": "bar"}

        validate(pyramid_request, {"document": document_data, "uri": target_uri})

        document_claims.document_uris_from_data.assert_called_once_with(
            document_data, claimant=target_uri
        )

    def test_it_puts_document_uris_in_appstruct(
        self, document_claims, pyramid_request, validate
    ):
        appstruct = validate(pyramid_request, {"document": {}})

        assert appstruct["document"]["document_uri_dicts"] == (
            document_claims.document_uris_from_data.return_value
        )

    def test_it_extracts_document_metas_from_the_document(
        self, document_claims, pyramid_request, validate
    ):
        document_data = {"foo": "bar"}
        target_uri = "http://example.com/example"

        validate(pyramid_request, {"document": {"foo": "bar"}, "uri": target_uri})

        document_claims.document_metas_from_data.assert_called_once_with(
            document_data, claimant=target_uri
        )

    def test_it_does_not_pass_modified_dict_to_document_metas_from_data(
        self, document_claims, pyramid_request, validate
    ):
        # If document_uris_from_data() modifies the document dict that it's
        # given, the original dict (or one with the same values as it) should be
        # passed t document_metas_from_data(), not the modified copy.

        document = {
            "top_level_key": "original_value",
            "sub_dict": {"key": "original_value"},
        }

        def document_uris_from_data(
            document, claimant  # pylint:disable=unused-argument
        ):
            document["new_key"] = "new_value"
            document["top_level_key"] = "new_value"
            document["sub_dict"]["key"] = "new_value"

        document_claims.document_uris_from_data.side_effect = document_uris_from_data

        validate(pyramid_request, {"document": document})

        assert document_claims.document_metas_from_data.call_args[0][0] == document

    def test_it_puts_document_metas_in_appstruct(
        self, document_claims, pyramid_request, validate
    ):
        appstruct = validate(pyramid_request, {"document": {}})

        assert appstruct["document"]["document_meta_dicts"] == (
            document_claims.document_metas_from_data.return_value
        )

    def test_it_clears_existing_keys_from_document(self, pyramid_request, validate):
        """
        Any keys in the document dict should be removed.

        They're replaced with the 'document_uri_dicts' and
        'document_meta_dicts' keys.

        """
        appstruct = validate(
            pyramid_request, {"document": {"foo": "bar"}}  # This should be deleted.
        )

        assert "foo" not in appstruct["document"]

    def test_document_does_not_end_up_in_extra(self, pyramid_request, validate):
        appstruct = validate(pyramid_request, {"document": {"foo": "bar"}})

        assert "document" not in appstruct.get("extra", {})

    def test_it_moves_extra_data_into_extra_sub_dict(self, pyramid_request, validate):
        appstruct = validate(
            pyramid_request,
            {
                # Throw in all the fields, just to make sure that none of them get
                # into extra.
                "created": "created",
                "updated": "updated",
                "user": "user",
                "id": "id",
                "uri": "uri",
                "text": "text",
                "tags": ["gar", "har"],
                "permissions": {"read": ["group:__world__"]},
                "target": [],
                "group": "__world__",
                "references": ["parent"],
                "flagged": True,
                # These should end up in extra.
                "foo": 1,
                "bar": 2,
            },
        )

        assert appstruct["extra"] == {"foo": 1, "bar": 2}

    def test_it_does_not_modify_extra_fields_that_are_not_sent(
        self, pyramid_request, validate
    ):
        appstruct = validate(pyramid_request, {"foo": "bar"})

        assert "custom" not in appstruct["extra"]

    def test_it_does_not_modify_extra_fields_if_none_are_sent(
        self, pyramid_request, validate
    ):
        appstruct = validate(pyramid_request, {})

        assert not appstruct.get("extra")


class TestCreateAnnotationSchema:
    def test_it_raises_if_data_has_no_uri(self, pyramid_request):
        data = self.valid_data()
        del data["uri"]
        schema = CreateAnnotationSchema(pyramid_request)

        with pytest.raises(ValidationError) as exc:
            schema.validate(data)

        assert str(exc.value) == "uri: 'uri' is a required property"

    def test_it_sets_userid(self, pyramid_config, pyramid_request):
        pyramid_config.testing_securitypolicy("acct:harriet@example.com")
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(self.valid_data())

        assert appstruct["userid"] == "acct:harriet@example.com"

    def test_it_inserts_empty_string_if_data_contains_no_text(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        assert not schema.validate(self.valid_data())["text"]

    def test_it_inserts_empty_list_if_data_contains_no_tags(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        assert schema.validate(self.valid_data())["tags"] == []

    def test_it_replaces_private_permissions_with_shared_False(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(
            self.valid_data(permissions={"read": ["acct:harriet@example.com"]})
        )

        assert not appstruct["shared"]
        assert "permissions" not in appstruct

    def test_it_replaces_shared_permissions_with_shared_True(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(
            self.valid_data(
                permissions={"read": ["group:__world__"]}, group="__world__"
            )
        )

        assert appstruct["shared"] is True
        assert "permissions" not in appstruct

    def test_it_defaults_to_private_if_no_permissions_object_sent(
        self, pyramid_request
    ):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(self.valid_data())

        assert not appstruct["shared"]

    def test_it_renames_group_to_groupid(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(self.valid_data(group="foo"))

        assert appstruct["groupid"] == "foo"
        assert "group" not in appstruct

    def test_it_inserts_default_groupid_if_no_group(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(self.valid_data())

        assert appstruct["groupid"] == "__world__"

    def test_it_keeps_references(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(
            self.valid_data(references=["parent id", "parent id 2"])
        )

        assert appstruct["references"] == ["parent id", "parent id 2"]

    def test_it_inserts_empty_list_if_no_references(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(self.valid_data())

        assert appstruct["references"] == []

    def test_it_deletes_groupid_for_replies(self, pyramid_request):
        schema = CreateAnnotationSchema(pyramid_request)

        appstruct = schema.validate(
            self.valid_data(group="foo", references=["parent annotation id"])
        )

        assert "groupid" not in appstruct

    def valid_data(self, **kwargs):
        """Return minimal valid data for creating a new annotation."""
        data = {"uri": "http://example.com/example"}
        data.update(kwargs)
        return data


class TestUpdateAnnotationSchema:
    def test_you_cannot_change_an_annotations_group(self, pyramid_request):
        schema = UpdateAnnotationSchema(pyramid_request, "", "")

        appstruct = schema.validate({"groupid": "new-group", "group": "new-group"})

        assert "groupid" not in appstruct
        assert "groupid" not in appstruct.get("extra", {})
        assert "group" not in appstruct
        assert "group" not in appstruct.get("extra", {})

    def test_you_cannot_change_an_annotations_userid(self, pyramid_request):
        schema = UpdateAnnotationSchema(pyramid_request, "", "")

        appstruct = schema.validate({"userid": "new_userid"})

        assert "userid" not in appstruct
        assert "userid" not in appstruct.get("extra", {})

    def test_you_cannot_change_an_annotations_references(self, pyramid_request):
        schema = UpdateAnnotationSchema(pyramid_request, "", "")

        appstruct = schema.validate({"references": ["new_parent"]})

        assert "references" not in appstruct
        assert "references" not in appstruct.get("extra", {})

    def test_it_replaces_private_permissions_with_shared_False(self, pyramid_request):
        schema = UpdateAnnotationSchema(pyramid_request, "", "")

        appstruct = schema.validate(
            {"permissions": {"read": ["acct:harriet@example.com"]}}
        )

        assert not appstruct["shared"]
        assert "permissions" not in appstruct
        assert "permissions" not in appstruct.get("extras", {})

    def test_it_replaces_shared_permissions_with_shared_True(self, pyramid_request):
        schema = UpdateAnnotationSchema(pyramid_request, "", "__world__")

        appstruct = schema.validate({"permissions": {"read": ["group:__world__"]}})

        assert appstruct["shared"] is True
        assert "permissions" not in appstruct
        assert "permissions" not in appstruct.get("extras", {})

    def test_it_passes_existing_target_uri_to_document_uris_from_data(
        self, document_claims, pyramid_request
    ):
        """
        If no 'uri' is given it should use the existing target_uri.

        If no 'uri' is given in the update request then
        document_uris_from_data() should be called with the existing
        target_uri of the annotation in the database.

        """
        document_data = {"foo": "bar"}
        schema = UpdateAnnotationSchema(pyramid_request, mock.sentinel.target_uri, "")

        schema.validate({"document": document_data})

        document_claims.document_uris_from_data.assert_called_once_with(
            document_data, claimant=mock.sentinel.target_uri
        )

    def test_it_passes_existing_target_uri_to_document_metas_from_data(
        self, document_claims, pyramid_request
    ):
        """
        If no 'uri' is given it should use the existing target_uri.

        If no 'uri' is given in the update request then
        document_metas_from_data() should be called with the existing
        target_uri of the annotation in the database.

        """
        document_data = {"foo": "bar"}
        schema = UpdateAnnotationSchema(pyramid_request, mock.sentinel.target_uri, "")

        schema.validate({"document": document_data})

        document_claims.document_metas_from_data.assert_called_once_with(
            document_data, claimant=mock.sentinel.target_uri
        )


class TestSearchParamsSchema:
    def test_it_returns_only_known_params(self, schema):
        expected_params = MultiDict(
            {
                "_separate_replies": True,
                "group": "group1",
                "quote": "quote me",
                "references": "3456TA12",
                "tag": "tagme",
                "tags": "tagme2",
                "text": "text me",
                "uri": "foobar.com",
                "uri.parts": "bbc",
                "wildcard_uri": "http://foo.com/*",
                "url": "https://foobar.com",
                "any": "foo",
                "user": "pooky",
                "sort": "created",
                "limit": 10,
                "order": "asc",
                "offset": 0,
                "search_after": "2018-01-01",
            }
        )
        input_params = NestedMultiDict(
            MultiDict(
                {
                    "_separate_replies": "1",
                    "group": "group1",
                    "quote": "quote me",
                    "references": "3456TA12",
                    "tag": "tagme",
                    "tags": "tagme2",
                    "text": "text me",
                    "uri": "foobar.com",
                    "uri.parts": "bbc",
                    "wildcard_uri": "http://foo.com/*",
                    "url": "https://foobar.com",
                    "any": "foo",
                    "user": "pooky",
                    "sort": "created",
                    "limit": "10",
                    "order": "asc",
                    "offset": "0",
                    "unknown": "no_exist",
                    "no_exist": "unknown",
                    "search_after": "2018-01-01",
                }
            )
        )

        params = validate_query_params(schema, input_params)

        assert params == expected_params

    @pytest.mark.parametrize(
        "key,examples",
        (
            ("url", ["http://foobar", "http://foobat"]),
            ("group", ["inu3340958u", "97jdm5o457"]),
        ),
    )
    def test_it_handles_duplicate_keys(self, schema, key, examples):
        expected_params = MultiDict([(key, example) for example in examples])
        input_params = deepcopy(expected_params)

        params = validate_query_params(schema, NestedMultiDict(input_params))
        assert params.getall(key) == examples

    def test_it_defaults_limit(self, schema):
        params = validate_query_params(schema, NestedMultiDict())

        assert params["limit"] == LIMIT_DEFAULT

    def test_it_defaults_offset(self, schema):
        params = validate_query_params(schema, NestedMultiDict())

        assert not params["offset"]

    def test_it_defaults_sort(self, schema):
        params = validate_query_params(schema, NestedMultiDict())

        assert params["sort"] == "updated"

    def test_it_defaults_order(self, schema):
        params = validate_query_params(schema, NestedMultiDict())

        assert params["order"] == "desc"

    def test_raises_if_invalid_sorting_order(self, schema):
        input_params = NestedMultiDict(MultiDict({"order": "notrecognized"}))

        with pytest.raises(ValidationError):
            validate_query_params(schema, input_params)

    def test_raises_if_invalid_sort(self, schema):
        input_params = NestedMultiDict(MultiDict({"sort": "notrecognized"}))

        with pytest.raises(ValidationError):
            validate_query_params(schema, input_params)

    @pytest.mark.parametrize("limit", (LIMIT_MAX + 1, -1))
    def test_raises_if_invalid_limit(self, schema, limit):
        input_params = NestedMultiDict(MultiDict({"limit": limit}))

        with pytest.raises(ValidationError):
            validate_query_params(schema, input_params)

    @pytest.mark.parametrize("offset", (OFFSET_MAX + 1, -1))
    def test_raises_if_invalid_offset(self, schema, offset):
        input_params = NestedMultiDict(MultiDict({"offset": offset}))

        with pytest.raises(ValidationError):
            validate_query_params(schema, input_params)

    def test_raises_if_invalid_search_after_date(self, schema):
        input_params = NestedMultiDict(MultiDict({"search_after": "invalid_date"}))

        with pytest.raises(ValidationError):
            validate_query_params(schema, input_params)

    @pytest.mark.parametrize(
        "search_after,sort",
        (
            ("2009-02-16", "updated"),
            ("2009-02", "updated"),
            ("2009", "updated"),
            ("2018-08-27T11:02:15.107224+00:00", "created"),
            ("5045000300.9", "updated"),
            ("8273640", "id"),
        ),
    )
    def test_passes_validation_if_valid_search_after(self, schema, search_after, sort):
        input_params = NestedMultiDict(
            MultiDict({"search_after": search_after, "sort": sort})
        )

        params = validate_query_params(schema, input_params)

        assert params["search_after"] == search_after

    def test_sets_offset_to_0_if_search_after(self, schema):
        input_params = NestedMultiDict(
            MultiDict({"search_after": "2009-02-16", "offset": 5})
        )

        params = validate_query_params(schema, input_params)

        assert not params["offset"]
        assert params["search_after"] == "2009-02-16"

    @pytest.mark.parametrize(
        "wildcard_uri", ("https://localhost:3000*", "file://localhost*/foo.pdf")
    )
    def test_raises_if_wildcards_are_in_domain(self, schema, wildcard_uri):
        input_params = NestedMultiDict(MultiDict({"wildcard_uri": wildcard_uri}))

        with pytest.raises(ValidationError):
            validate_query_params(schema, input_params)

    @pytest.fixture
    def schema(self):
        return SearchParamsSchema()


class TestURLMigrationSchema:
    def test_it_validates_valid_data(self, validate):
        validate(
            {
                "https://example.com": {
                    "url": "https://example.org",
                    "document": {"title": "The new Example.com"},
                    "selector": [{"type": "PageSelector", "index": 2, "label": "3"}],
                }
            }
        )

    def test_it_accepts_minimal_data(self, validate):
        validate(
            {
                "https://example.com": {
                    "url": "https://example.org",
                }
            }
        )

    def test_it_raises_for_invalid_source_url(self, validate):
        with pytest.raises(ValidationError, match="not-a-url.*does not match"):
            validate({"not-a-url": {"url": "https://foobar.org"}})

    def test_it_raises_for_invalid_dest_url(self, validate):
        with pytest.raises(ValidationError, match="also-not-a-url.*does not match"):
            validate({"https://example.com": {"url": "also-not-a-url"}})

    def test_it_raises_if_new_url_missing(self, validate):
        with pytest.raises(ValidationError, match="url.*required"):
            validate({"https://example.com": {}})

    @pytest.fixture
    def validate(self):
        return URLMigrationSchema().validate


@pytest.fixture
def document_claims(patch):
    return patch("h.schemas.annotation.document_claims")
