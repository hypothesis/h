import pytest

from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)
from h.h_api.exceptions import SchemaValidationError


class TestUpsertUser:
    def test_create_ok(self, user_attributes):
        data = UpsertUser.create(user_attributes, "user_ref")
        assert data.raw == {
            "data": {
                "type": "user",
                "meta": {
                    "$anchor": "user_ref",
                    "query": {"authority": "example.com", "username": "username",},
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
            UpsertUser.create({}, "id_ref")


class TestUpsertGroup:
    def test_create_ok(self, group_attributes):
        data = UpsertGroup.create(group_attributes, "reference")

        assert data.raw == {
            "data": {
                "attributes": {"name": "name"},
                "meta": {
                    "$anchor": "reference",
                    "query": {"groupid": "group:name@example.com"},
                },
                "type": "group",
            }
        }

    def test_create_can_fail(self):
        with pytest.raises(Exception):
            UpsertGroup.create({}, None)


class TestCreateGroupMembership:
    def test_create_ok(self):
        data = CreateGroupMembership.create("user_ref", "group_ref")

        assert data.raw == {
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

        assert body.member.id is None
        assert body.member.ref == "user_ref"
        assert body.group.id is None
        assert body.group.ref == "group_ref"
