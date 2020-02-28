from functools import lru_cache

from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.bulk_api.model.data_body import (
    CreateGroupMembership,
    UpsertGroup,
    UpsertUser,
)
from h.h_api.enums import CommandType, DataType
from h.h_api.model.base import Model
from h.h_api.schema import Schema


class Command(Model):
    """A single abstract command provided to the API."""

    schema = Schema.get_validator("bulk_api/wrapper.json")
    validation_error_title = "Command wrapper is malformed: cannot interpret command"

    def validate(self):
        super().validate()
        if isinstance(self.body, Model):
            self.body.validate()

    @classmethod
    def create(cls, _type, body):
        """
        Create a command.

        :param _type: The CommandType of the command
        :param body: The payload for the command
        :return: An instance of Command
        """
        return cls([CommandType(_type).value, cls.extract_raw(body)])

    @property
    def type(self):
        """
        Get the command type.

        :return: The CommandType of this command
        """
        return CommandType(self.raw[0])

    @property
    def body(self):
        """
        Get the body of this command.

        :return: The raw body
        """
        return self.raw[1]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.body}>"


class ConfigCommand(Command):
    @classmethod
    def create(cls, config):
        return super().create(CommandType.CONFIGURE, cls.extract_raw(config))

    @property
    @lru_cache(1)
    def body(self):
        return Configuration(self.raw[1])


class DataCommand(Command):
    data_classes = None

    @property
    @lru_cache(1)
    def body(self):
        body = super().body

        data_type = DataType(body["data"]["type"])

        try:
            klass = self.data_classes[data_type]

        except KeyError:
            # TODO! A custom error would be nice here
            raise TypeError("Invalid action on data type")

        # Don't validate this all the time, we did it on the way in. If we have
        # mutated it it might not match the schema we except from clients, but
        # it's still valid
        return klass(body, validate=False)

    @classmethod
    def prepare_for_execute(cls, batch, default_config):
        pass


class CreateCommand(DataCommand):
    data_classes = {DataType.GROUP_MEMBERSHIP: CreateGroupMembership}


class UpsertCommand(DataCommand):
    data_classes = {
        DataType.GROUP: UpsertGroup,
        DataType.USER: UpsertUser,
    }
