from h.h_api.bulk_api.model.command import ConfigCommand, CreateCommand, UpsertCommand
from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)
from h.h_api.enums import CommandType


class CommandBuilder:
    @classmethod
    def from_data(cls, raw):
        command_type = CommandType(raw[0])

        if command_type is CommandType.CONFIGURE:
            return ConfigCommand(raw)

        if command_type is CommandType.CREATE:
            return CreateCommand(raw)

        elif command_type is CommandType.UPSERT:
            return UpsertCommand(raw)

    @classmethod
    def configure(cls, effective_user, total_instructions):
        return ConfigCommand.create(
            Configuration.create(effective_user, total_instructions),
        )

    class user:
        @classmethod
        def upsert(cls, user_id, attributes):
            return UpsertCommand.create(
                CommandType.UPSERT, UpsertUser.create(user_id, attributes)
            )

    class group:
        @classmethod
        def upsert(cls, attributes, id_reference):
            return UpsertCommand.create(
                CommandType.UPSERT, UpsertGroup.create(attributes, id_reference)
            )

    class group_membership:
        @classmethod
        def create(cls, user_id, group_ref):
            return CreateCommand.create(
                CommandType.CREATE, CreateGroupMembership.create(user_id, group_ref)
            )
