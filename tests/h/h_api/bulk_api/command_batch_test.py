from unittest.mock import Mock

import pytest
from h_matchers import Any

from h.h_api.bulk_api.command_batch import CommandBatch
from h.h_api.bulk_api.command_builder import CommandBuilder
from h.h_api.exceptions import CommandSequenceException


class TestCommandBatch:
    def test_flushing_does_nothing_with_an_empty_batch(self, batch, on_flush):
        batch.flush()

        on_flush.assert_not_called()

    def test_flushing_resets_the_batch(self, batch, command):
        self.add_commands(batch, [command])
        assert batch.batch is not None

        batch.flush()

        assert batch.batch is None

    def test_flushing_calls_on_flush_callback(self, batch, on_flush, command):
        self.add_commands(batch, [command, command])

        batch.flush()

        on_flush.assert_called_once_with(
            command.type, command.body.type, [command, command]
        )

    def test_add_adds_to_batch(self, batch, command):
        self.add_commands(batch, [command])

        assert batch.batch == [command]

    def test_add_causes_flush_if_we_exceed_batch_size(self, batch, on_flush, command):
        batch.batch_size = 2

        self.add_commands(batch, [command])
        on_flush.assert_not_called()

        self.add_commands(batch, [command])
        on_flush.assert_called_once()

    def test_add_flushes_after_body_as_context_manager(self, batch, on_flush, command):
        batch.batch_size = 1

        with batch.add(command):
            on_flush.assert_not_called()

        on_flush.assert_called_once()

    def test_add_causes_flush_if_we_change_command_type(
        self, batch, on_flush, command, other_command
    ):
        self.add_commands(batch, [command])
        batch.batch = [command]
        on_flush.assert_not_called()

        with batch.add(other_command):
            on_flush.assert_called_once_with(Any(), Any(), [command])

        batch.batch = [other_command]

    def test_add_fails_if_we_return_to_a_command_type(
        self, batch, on_flush, command, other_command
    ):
        self.add_commands(batch, [command, other_command])

        with pytest.raises(CommandSequenceException):
            self.add_commands(batch, [command])

    @staticmethod
    def add_commands(batch, commands):
        # `add()` is a context manager, which makes sense in use, but is a bit
        # of a pain for us

        for command in commands:
            with batch.add(command):
                pass

    @pytest.fixture
    def command(self, user_attributes):
        return CommandBuilder.user.upsert("acct:user@example.com", user_attributes)

    @pytest.fixture
    def other_command(self, group_attributes):
        return CommandBuilder.group.upsert(group_attributes, "id_ref")

    @pytest.fixture
    def on_flush(self):
        def _on_flush(command_type, data_type, batch):
            pass

        return Mock(spec=_on_flush)

    @pytest.fixture
    def batch(self, on_flush):
        return CommandBatch(on_flush)
