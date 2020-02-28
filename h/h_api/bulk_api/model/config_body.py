"""Models representing the configuration."""

from collections import defaultdict
from functools import lru_cache

from h.h_api.enums import CommandType, DataType
from h.h_api.model.base import Model
from h.h_api.schema import Schema


class Configuration(Model):
    validator = Schema.get_validator("bulk_api/command/configuration.json")

    WILD_CARD = "*"

    @classmethod
    def create(cls, effective_user, total_instructions):
        """
        Create a configuration object.

        :param effective_user: User to execute the command as
        :param total_instructions: Number of instructions (including this)
        """
        return cls(
            {
                "view": None,
                "user": {"effective": effective_user},
                "instructions": {"total": int(total_instructions)},
                "defaults": [
                    ["create", "*", {"on_duplicate": "continue"}],
                    ["upsert", "*", {"merge_query": True}],
                ],
            }
        )

    @property
    def view(self):
        """The return type of view requested by the user."""
        return self.raw["view"]

    @property
    def effective_user(self):
        """The user to execute the request as."""
        return self.raw["user"]["effective"]

    @property
    def total_instructions(self):
        """
        The number of instructions in the request.

        This count includes configuration commands.
        """
        return self.raw["instructions"]["total"]

    def defaults_for(self, command_type, data_type):
        """
        Provide default configuration for the given command and data type.

        This will use any wild card options first, overlaying more specific
        defaults as they are found.

        :param command_type: Type of modification (e.g. Types.UPSERT)
        :param data_type: Data type being modified
        :return: A dict of config
        """
        defaults = self._command_defaults

        config = {}

        wild = defaults.get(self.WILD_CARD, {})
        specific = defaults.get(CommandType(command_type), {})
        data_type = DataType(data_type)

        for container in (wild, specific):
            if self.WILD_CARD in container:
                config.update(container[self.WILD_CARD])

            if data_type in container:
                config.update(container[data_type])

        return config

    @property
    @lru_cache(1)
    def _command_defaults(self):
        config = defaultdict(dict)

        for command_type, data_type, defaults in self.raw["defaults"]:
            if command_type != self.WILD_CARD:
                command_type = CommandType(command_type)

            if data_type != self.WILD_CARD:
                data_type = DataType(data_type)

            config[command_type][data_type] = defaults

        return config
