"""Models representing the data modifying payloads."""

from h.h_api.enums import DataType
from h.h_api.model.json_api import JSONAPIData
from h.h_api.schema import Schema


class UpsertUser(JSONAPIData):
    """The data to upsert a user."""

    schema = Schema.get_validator("bulk_api/command/upsert_user.json")

    @classmethod
    def create(cls, _id, attributes):
        """
        Create an upsert user body.

        :param _id: User id
        :param attributes: User attributes
        :return:
        """
        return super().create(DataType.USER, _id=_id, attributes=attributes)


class UpsertGroup(JSONAPIData):
    """The data to upsert a group."""

    schema = Schema.get_validator("bulk_api/command/upsert_group.json")

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

    schema = Schema.get_validator("bulk_api/command/create_group_membership.json")

    @classmethod
    def create(cls, user_id, group_ref):
        """
        Create a create group membership body for adding users to groups.

        :param user_id: User id
        :param group_ref: Custom group reference
        :return:
        """
        return super().create(
            DataType.GROUP_MEMBERSHIP,
            relationships={
                "member": {"data": {"type": DataType.USER.value, "id": user_id}},
                "group": {
                    "data": {"type": DataType.GROUP.value, "id": {"$ref": group_ref}}
                },
            },
        )
