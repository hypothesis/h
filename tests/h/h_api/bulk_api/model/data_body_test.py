import pytest

from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertBody,
    UpsertGroup,
    UpsertUser,
)
from h.h_api.enums import DataType
from h.h_api.exceptions import SchemaValidationError


class TestUpsertBody:
    class Subclass(UpsertBody):
        data_type = DataType.GROUP
        query_fields = ["query_field"]

    def test_create_ok(self, body):
        assert body.raw == {
            "data": {
                "type": "group",
                "meta": {"query": {"query_field": "query"}, "$anchor": "id_ref"},
                "attributes": {"non_query_field": "non_query"},
            }
        }

    def test_query(self, body):
        assert body.query == {"query_field": "query"}

    @pytest.fixture
    def body(self):
        class SubClass(UpsertBody):
            data_type = DataType.GROUP
            query_fields = ["query_field"]

        return SubClass.create(
            {"query_field": "query", "non_query_field": "non_query"}, "id_ref"
        )


class TestUpsertUser:
    def test_create_ok(self, user_attributes):
        body = UpsertUser.create(user_attributes, "user_ref")

        assert body.raw == {
            "data": {
                "type": "user",
                "meta": {
                    "$anchor": "user_ref",
                    "query": {"authority": "example.com", "username": "username"},
                },
                "attributes": {
                    "identities": [
                        {
                            "provider": "provider string",
                            "provider_unique_id": "provider unique id",
                        }
                    ],
                    "display_name": "display name",
                },
            }
        }

    def test_create_can_fail(self):
        with pytest.raises(SchemaValidationError):
            UpsertUser.create({}, None)


class TestUpsertGroup:
    def test_create_ok(self, group_attributes):
        body = UpsertGroup.create(group_attributes, "reference")

        assert body.raw == {
            "data": {
                "attributes": {"name": "name"},
                "meta": {
                    "$anchor": "reference",
                    "query": {
                        "authority": "example.com",
                        "authority_provided_id": "authority_provided_id",
                    },
                },
                "type": "group",
            }
        }

    def test_create_can_fail(self):
        with pytest.raises(Exception):
            UpsertGroup.create({}, None)


class TestCreateGroupMembership:
    def test_create_ok(self):
        body = CreateGroupMembership.create("user_ref", "group_ref")

        assert body.raw == {
            "data": {
                "relationships": {
                    "member": {"data": {"id": {"$ref": "user_ref"}, "type": "user"}},
                    "group": {"data": {"id": {"$ref": "group_ref"}, "type": "group"}},
                },
                "type": "group_membership",
            }
        }

    def test_create_can_fail(self):
        with pytest.raises(SchemaValidationError):
            CreateGroupMembership.create("bad", None)

    def test_validation_can_fail(self):
        with pytest.raises(SchemaValidationError):
            CreateGroupMembership(
                {
                    "data": {
                        "type": "group_membership",
                        "relationships": {
                            # This isn't good enough, these should have bodies
                            "member": {},
                            "group": {},
                        },
                    }
                }
            )

    def test_accessors(self, create_group_membership_body):
        body = CreateGroupMembership(create_group_membership_body)

        assert body.member_id == "acct:user@example.com"
        assert body.group_id is None
        assert body.group_ref == "thing"
