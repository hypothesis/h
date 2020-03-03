from copy import deepcopy
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

    validator = Schema.get_validator("bulk_api/wrapper.json")
    validation_error_title = "Cannot interpret command as the wrapper is malformed"

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
    """A command containing job configuration instructions."""

    @classmethod
    def create(cls, config):
        """
        Create a new ConfigCommand from a configuration instance.

        :param config: A Configuration object
        :return: A ConfigCommand containing that config
        """
        return super().create(CommandType.CONFIGURE, cls.extract_raw(config))

    @property
    @lru_cache(1)
    def body(self):
        """
        Get the body of this command.

        :return: A Configuration object
        """
        return Configuration(self.raw[1])


class DataCommand(Command):
    """Abstract command class for commands which alter data in the database.

    This object will interpret the instructions given to it and return an
    appropriate body object based on the contents.

    The types must be specified using the `data_classes` dict which maps from
    `DataType` to the class implementing the body. The body should be a child
    of `JSONAPIData`.
    """

    data_classes = None

    @property
    @lru_cache(1)
    def body(self):
        """
        Get the appropriate body object for this command,

        :return: A different class depending on `DataType` and `data_classes`
        :raise KeyError: If no type can be found for the given `DataType`
        """
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
    """A command to create an object in the database."""

    data_classes = {DataType.GROUP_MEMBERSHIP: CreateGroupMembership}


class UpsertCommand(DataCommand):
    """A command to upsert an object in the database."""

    data_classes = {
        DataType.GROUP: UpsertGroup,
        DataType.USER: UpsertUser,
    }

    @classmethod
    def prepare_for_execute(cls, batch, default_config):
        # Pop out this command as it's just for us
        merge_query = default_config.pop("merge_query", None)

        if not merge_query:
            return

        for command in batch:
            query = command.body.meta.get("query")
            if not query:
                continue

            new_attrs = deepcopy(query)
            new_attrs.update(command.body.attributes)

            command.body.attributes = new_attrs
