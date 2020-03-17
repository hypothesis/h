from unittest.mock import call, create_autospec

import pytest
from h_matchers import Any

# Import... ALL OF THE THINGS
from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.bulk_api.command_processor import CommandProcessor
from h.h_api.bulk_api.model.report import Report
from h.h_api.bulk_api.observer import Observer
from h.h_api.enums import CommandResult, CommandStatus, CommandType, DataType
from h.h_api.exceptions import CommandSequenceError, InvalidDeclarationError


class TestCommandProcessor:
    def test_configuration_command_is_required_first(
        self, command_processor, user_command
    ):
        with pytest.raises(CommandSequenceError):
            command_processor.process([user_command])

    def test_multi_configuration_not_permitted(self, command_processor, config_command):
        with pytest.raises(CommandSequenceError):
            command_processor.process([config_command, config_command])

    def test_if_fails_with_no_commands(self, command_processor):
        with pytest.raises(CommandSequenceError):
            command_processor.process([])

    def test_it_fails_with_too_many_commands(
        self, command_processor, commands, user_command
    ):
        commands.append(user_command)

        with pytest.raises(InvalidDeclarationError):
            command_processor.process(commands)

    def test_it_fails_with_too_few_commands(
        self, command_processor, commands, user_command
    ):
        commands.pop()

        with pytest.raises(InvalidDeclarationError):
            command_processor.process(commands)

    def test_id_references_are_dereferenced(
        self, command_processor, config_command, membership_command, group_command
    ):
        command_processor.id_refs.add_concrete_id(
            DataType.GROUP, group_command.body.id_reference, "concrete_id"
        )

        assert membership_command.body.relationships["group"]["data"]["id"] == {
            "$ref": group_command.body.id_reference
        }

        command_processor.process([config_command, membership_command])

        assert (
            membership_command.body.relationships["group"]["data"]["id"]
            == "concrete_id"
        )

    def test_it_passes_commands_to_the_observer(
        self, command_processor, observer, config_command, user_command
    ):
        command_processor.process([config_command, user_command])

        observer.observe_command.assert_has_calls(
            [
                call(config_command, status=CommandStatus.AS_RECEIVED),
                call(config_command, status=CommandStatus.POST_EXECUTE),
                call(user_command, status=CommandStatus.AS_RECEIVED),
                call(user_command, status=CommandStatus.POST_EXECUTE),
            ]
        )

    def test_configuration_commands_are_passed_to_the_executor(
        self, command_processor, executor, config_command, user_command
    ):
        command_processor.process([config_command, user_command])

        executor.configure.assert_called_once_with(config_command.body)

    def test_all_items_are_flushed_to_executor(
        self, command_processor, executor, user_command, group_command
    ):
        config = CommandBuilder.configure(
            effective_user="acct:user@example.com", total_instructions=5
        )

        command_processor.process(
            [config, user_command, user_command, group_command, group_command]
        )

        executor.execute_batch.assert_has_calls(
            [
                call(
                    batch=[user_command, user_command],
                    command_type=CommandType.UPSERT,
                    data_type=DataType.USER,
                    default_config=Any.dict(),
                ),
                call(
                    batch=[group_command, group_command],
                    command_type=CommandType.UPSERT,
                    data_type=DataType.GROUP,
                    default_config=Any.dict(),
                ),
            ]
        )

    def test_items_are_prepared_for_the_executor(
        self, command_processor, executor, config_command, group_command
    ):
        config_command.body.defaults_for = create_autospec(
            config_command.body.defaults_for
        )
        config_command.body.defaults_for.return_value = {"some_param": 1}

        # I'd like to mock out the class level method, but I can't work out how
        # without redefining it forever
        group_command.prepare_for_execute = create_autospec(
            group_command.prepare_for_execute
        )

        command_processor.process([config_command, group_command])

        group_command.prepare_for_execute.assert_called_once_with(
            [group_command], {"some_param": 1}
        )

    @pytest.mark.parametrize(
        "bad_reports,exception",
        (
            ("string", TypeError),
            (["not_a_report_class"], TypeError),
            ([], IndexError),
            (
                [
                    Report(CommandResult.CREATED, id_="foo"),
                    Report(CommandResult.CREATED, id_="foo"),
                ],
                IndexError,
            ),
        ),
    )
    def test_we_require_a_report_for_each_object(
        self, command_processor, executor, commands, bad_reports, exception
    ):
        executor.execute_batch.side_effect = None
        executor.execute_batch.return_value = bad_reports

        with pytest.raises(exception):
            command_processor.process(commands)

    @pytest.mark.xfail
    def test_reports_are_stored_if_view_is_not_None(
        self, command_processor, commands, config_command
    ):
        config_command.body.raw["view"] = "to_be_decided"

        command_processor.process(commands)

        assert command_processor.reports == Any.dict.containing(
            {DataType.USER: [Any.instance_of(Report)]}
        )

    def test_reports_are_not_stored_if_view_is_None(
        self, command_processor, commands, config_command
    ):
        assert config_command.body.view is None

        command_processor.process(commands)

        assert not command_processor.reports

    @pytest.fixture
    def commands(self, config_command, user_command):
        return [config_command, user_command]

    @pytest.fixture
    def command_processor(self, executor, observer):
        return CommandProcessor(executor, observer)

    @pytest.fixture
    def observer(self):
        return create_autospec(Observer, instance=True)
