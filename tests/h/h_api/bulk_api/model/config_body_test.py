import pytest

from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.enums import CommandType, DataType
from h.h_api.exceptions import SchemaValidationError


class TestConfiguration:
    def test_from_raw(self, configuration_body):
        config = Configuration(configuration_body)

        assert isinstance(config, Configuration)
        assert config.raw == configuration_body

    def test_create(self):
        config = Configuration.create(
            effective_user="acct:user@example.com", total_instructions="100"
        )

        assert isinstance(config, Configuration)

        assert config.raw == {
            "view": None,
            "user": {"effective": "acct:user@example.com"},
            "instructions": {"total": 100},
            "defaults": [
                ["create", "*", {"on_duplicate": "continue"}],
                ["upsert", "*", {"merge_query": True}],
            ],
        }

    def test_we_apply_the_schema(self):
        with pytest.raises(SchemaValidationError):
            Configuration.create("wrong_user_format", 100)

    def test_accessors(self):
        config = Configuration.create(
            effective_user="acct:user@example.com", total_instructions=100
        )

        assert config.view is None
        assert config.effective_user == "acct:user@example.com"
        assert config.total_instructions == 100

    @pytest.mark.parametrize(
        "command_type,data_type,expected_defaults",
        (
            (CommandType.UPSERT, DataType.GROUP, {"a": 1, "last": "wild"}),
            (CommandType.CREATE, DataType.GROUP, {"a": 1, "b": 2, "last": "command"}),
            (CommandType.UPSERT, DataType.USER, {"a": 1, "c": 3, "last": "data"}),
            (
                CommandType.CREATE,
                DataType.USER,
                {"a": 1, "b": 2, "c": 3, "d": 4, "last": "both"},
            ),
            (
                CommandType.CREATE.value,
                DataType.USER.value,
                {"a": 1, "b": 2, "c": 3, "d": 4, "last": "both"},
            ),
        ),
    )
    def test_defaults_for(self, command_type, data_type, expected_defaults):
        config = Configuration.create("acct:user@example.com", 2)

        config.raw["defaults"] = [
            ["*", "*", {"a": 1, "last": "wild"}],
            ["create", "*", {"b": 2, "last": "command"}],
            ["*", "user", {"c": 3, "last": "data"}],
            ["create", "user", {"d": 4, "last": "both"}],
        ]

        defaults = config.defaults_for(command_type, data_type)

        assert defaults == expected_defaults
