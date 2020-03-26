"""Models representing the data modifying payloads."""

from h.h_api.enums import DataType
from h.h_api.model.json_api import JSONAPIData
from h.h_api.schema import Schema


class UpsertBody(JSONAPIData):
    data_type = None
    query_fields = []

    @classmethod
    def create(cls, attributes, id_reference):
        query = {field: attributes.pop(field, None) for field in cls.query_fields}

        return super().create(
            data_type=cls.data_type,
            attributes=attributes,
            meta={"query": query},
            id_reference=id_reference,
        )

    @property
    def query(self):
        """The query used to select which item to update."""

        return self.meta["query"]


class UpsertUser(UpsertBody):
    """The data to upsert a user."""

    validator = Schema.get_validator("bulk_api/command/upsert_user.json")
    data_type = DataType.USER
    query_fields = ["authority", "username"]


class UpsertGroup(UpsertBody):
    """The data to upsert a group."""

    validator = Schema.get_validator("bulk_api/command/upsert_group.json")
    data_type = DataType.GROUP
    query_fields = ["authority", "authority_provided_id"]


class CreateGroupMembership(JSONAPIData):
    """The data to add a user to a group."""

    validator = Schema.get_validator("bulk_api/command/create_group_membership.json")

    @classmethod
    def create(cls, user_ref, group_ref):
        """
        Create a create group membership body for adding users to groups.

        :param user_ref: Custom user reference
        :param group_ref: Custom group reference
        :return:
        """
        return super().create(
            DataType.GROUP_MEMBERSHIP,
            relationships={
                "member": {
                    "data": {"type": DataType.USER.value, "id": {"$ref": user_ref}}
                },
                "group": {
                    "data": {"type": DataType.GROUP.value, "id": {"$ref": group_ref}}
                },
            },
        )

    @property
    def member_id(self):
        """The user which is a member of this group."""

        _member_id = self._member_id
        if "$ref" in _member_id:
            return None

        return _member_id

    @property
    def group_id(self):
        """The group the user is a member of."""

        _group_id = self._group_id
        if "$ref" in _group_id:
            return None

        return _group_id

    @property
    def group_ref(self):
        """
        A client provided reference for this group.

        If you don't know the group id yet, you can use your own reference.
        """
        return self._group_id.get("$ref")

    @property
    def member_ref(self):
        """
        A client provided reference for this member.

        If you don't know the member id yet, you can use your own reference.
        """
        return self._member_id.get("$ref")

    @property
    def _member_id(self):
        return self.relationships["member"]["data"]["id"]

    @property
    def _group_id(self):
        return self.relationships["group"]["data"]["id"]
