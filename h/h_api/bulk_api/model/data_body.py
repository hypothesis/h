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
    def member(self):
        """The user which is a member of this group.

        :return: A value object with `id` and `ref` properties.
        """
        return _IdRef(self.relationships["member"]["data"]["id"])

    @property
    def group(self):
        """The group which this user is a member of.

        :return: A value object with `id` and `ref` properties.
        """
        return _IdRef(self.relationships["group"]["data"]["id"])


class _IdRef:
    """A value object which represents an id reference or concrete id."""

    def __init__(self, value):
        if isinstance(value, dict):
            self.id, self.ref = None, value.get("$ref")
        else:
            self.id, self.ref = value, None
