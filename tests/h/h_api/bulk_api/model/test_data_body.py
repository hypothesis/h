import pytest

from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)


class TestUpsertUser:
    def test_create_ok(self, user_attributes):
        data = UpsertUser.create("acct:user@example.com", user_attributes)
        assert data.raw == {
            "data": {
                "attributes": {
                    "authority": "example.com",
                    "display_name": "display name",
                    "identities": [
                        {
                            "provider": "provider string",
                            "provider_unique_id": "provider " "unique id",
                        }
                    ],
                    "username": "user",
                },
                "id": "acct:user@example.com",
                "type": "user",
            }
        }

    def test_create_can_fail(self):
        with pytest.raises(Exception):
            UpsertUser.create("bad", {})


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
        data = CreateGroupMembership.create("acct:user@example.com", "reference")

        assert data.raw == {
            "data": {
                "relationships": {
                    "group": {"data": {"id": {"$ref": "reference"}, "type": "group"}},
                    "member": {"data": {"id": "acct:user@example.com", "type": "user"}},
                },
                "type": "group_membership",
            }
        }

    def test_create_can_fail(self,):
        with pytest.raises(Exception):
            CreateGroupMembership.create("bad", None)

    def test_accessors(self, create_group_membership_body):
        data = CreateGroupMembership(create_group_membership_body)

        assert data.member_id == "acct:user@example.com"
        assert data.group_id is None
        assert data.group_ref == "thing"
