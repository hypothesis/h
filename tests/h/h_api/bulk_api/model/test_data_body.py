import pytest

from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)


class TestUpsertUser:
    def test_create_ok(self, user_attributes):
        UpsertUser.create("acct:user@example.com", user_attributes)

    def test_create_can_fail(self):
        with pytest.raises(Exception):
            UpsertUser.create("bad", {})


class TestUpsertGroup:
    def test_create_ok(self, group_attributes):
        UpsertGroup.create(group_attributes, "reference")

    def test_create_can_fail(self):
        with pytest.raises(Exception):
            UpsertGroup.create({}, None)


class TestCreateGroupMembership:
    def test_create_ok(self):
        CreateGroupMembership.create("acct:user@example.com", "reference")

    def test_create_can_fail(self,):
        with pytest.raises(Exception):
            CreateGroupMembership.create("bad", None)
