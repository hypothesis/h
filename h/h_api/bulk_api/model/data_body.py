"""Models representing the data modifying payloads."""

from h.h_api.enums import DataType
from h.h_api.model.json_api import JSONAPIData
from h.h_api.schema import Schema


class UpsertUser(JSONAPIData):
    """The data to upsert a user."""

    validator = Schema.get_validator("bulk_api/command/upsert_user.json")

    @classmethod
    def create(cls, attributes, id_reference):
        """
        Create an upsert user body.

        :param _id: User id
        :param attributes: User attributes
        :return:
        """
        return super().create(
            DataType.USER, attributes=attributes, meta={"$anchor": id_reference}
        )


class UpsertGroup(JSONAPIData):
    """The data to upsert a group."""

    validator = Schema.get_validator("bulk_api/command/upsert_group.json")

    @classmethod
    def create(cls, attributes, id_reference):
        """
        Create an upsert group body.

        :param attributes: Group attributes
        :param id_reference: A custom reference for this group
        :return:
        """
        group_id = attributes.pop("groupid", None)

        return super().create(
            DataType.GROUP,
            attributes=attributes,
            meta={"query": {"groupid": group_id}, "$anchor": id_reference},
        )


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
