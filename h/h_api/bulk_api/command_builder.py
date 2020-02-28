"""Tools for deserialising and creating command objects."""
from h.h_api.bulk_api.model.command import ConfigCommand, CreateCommand, UpsertCommand
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)
from h.h_api.enums import CommandType


class CommandBuilder:
    """A class for creating commands."""

    @classmethod
    def from_data(cls, raw):
        """Create a command from a raw data structure.

        :param raw: The data to decode
        :returns: An appropriate child of `Command`
        """
        command_type = CommandType(raw[0])

        if command_type is CommandType.CONFIGURE:
            return ConfigCommand(raw)

        if command_type is CommandType.CREATE:
            return CreateCommand(raw)

        elif command_type is CommandType.UPSERT:
            return UpsertCommand(raw)

    @classmethod
    def configure(cls, effective_user, total_instructions):
        """
        Create a configuration command.

        :param effective_user: The user to execute actions as
        :param total_instructions: The total number of instructions
        :rtype: ConfigCommand
        """
        return ConfigCommand.create(
            Configuration.create(effective_user, total_instructions),
        )

    class user:
        """User commands."""

        @classmethod
        def upsert(cls, user_id, attributes):
            """
            Create a user upsert command.

            :param user_id: Users id (e.g. 'acct:user@example.com')
            :param attributes: Dict of user fields and values
            :rtype: UpsertCommand
            """
            return UpsertCommand.create(
                CommandType.UPSERT, UpsertUser.create(user_id, attributes)
            )

    class group:
        """Group commands."""

        @classmethod
        def upsert(cls, attributes, id_reference):
            """
            Create a group upsert command.

            :param attributes: Dict of group fields and values
            :param id_reference: Custom reference to this group
            :rtype: UpsertCommand
            """
            return UpsertCommand.create(
                CommandType.UPSERT, UpsertGroup.create(attributes, id_reference)
            )

    class group_membership:
        """Group membership commands."""

        @classmethod
        def create(cls, user_id, group_ref):
            """
            Create a group membership create.

            As the group id is not known at command creation time, a custom
            reference can be supplied to the group which is then used here to
            link the two.

            :param user_id: The user id
            :param group_ref: Custom reference to the group
            :rtype: CreateCommand
            """
            return CreateCommand.create(
                CommandType.CREATE, CreateGroupMembership.create(user_id, group_ref)
            )
