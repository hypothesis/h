from unittest.mock import sentinel

import pytest
from pytest import param

from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.enums import CommandType, DataType
from h.h_api.exceptions import InvalidDeclarationError, UnsupportedOperationError
from h.services.bulk_executor._executor import BulkExecutor
from tests.h.services.bulk_executor.conftest import CommandFactory


class TestDBExecutor:
    @pytest.mark.parametrize(
        "command_type,data_type,handler",
        (
            param(
                CommandType.UPSERT,
                DataType.USER,
                "UserUpsertAction",
                marks=pytest.mark.xfail(reason="Not implemented"),
            ),
            param(
                CommandType.UPSERT,
                DataType.GROUP,
                "GroupUpsertAction",
                marks=pytest.mark.xfail(reason="Not implemented"),
            ),
            param(
                CommandType.CREATE,
                DataType.GROUP_MEMBERSHIP,
                "GroupMembershipCreateAction",
                marks=pytest.mark.xfail(reason="Not implemented"),
            ),
        ),
        indirect=["handler"],
    )
    def test_it_calls_correct_db_handler(
        self, db_session, command_type, data_type, handler, commands
    ):
        executor = BulkExecutor(db_session)
        handler.assert_called_once_with(db_session)

        executor.effective_user_id = 1

        # These commands aren't actually the right type, but it doesn't
        # matter for this test
        executor.execute_batch(
            command_type, data_type, {"config_option": 2}, commands,
        )

        bulk_upsert = handler.return_value
        bulk_upsert.execute.assert_called_once_with(
            commands, effective_user_id=1, config_option=2
        )

    @pytest.mark.parametrize(
        "command_type,data_type",
        (
            (CommandType.CREATE, DataType.USER),
            (CommandType.CREATE, DataType.GROUP),
            (CommandType.UPSERT, DataType.GROUP_MEMBERSHIP),
        ),
    )
    def test_it_raises_UnsupportedOperationError_for_invalid_actions(
        self, db_session, command_type, data_type, commands
    ):
        executor = BulkExecutor(db_session)

        with pytest.raises(UnsupportedOperationError):
            executor.execute_batch(command_type, data_type, commands, {})

    def test_it_raises_InvalidDeclarationError_with_non_lms_authority(self):
        config = Configuration.create(
            effective_user="acct:user@bad_authority.com", total_instructions=2
        )

        with pytest.raises(InvalidDeclarationError):
            BulkExecutor(sentinel.db).configure(config)

    @pytest.mark.parametrize(
        "command",
        (
            param(CommandFactory.user_upsert(authority="bad"), id="bad user attr"),
            param(
                CommandFactory.user_upsert(query_authority="bad"), id="bad user query"
            ),
            param(CommandFactory.group_upsert(authority="bad"), id="bad group attr"),
            param(
                CommandFactory.group_upsert(query_authority="bad"), id="bad group query"
            ),
        ),
    )
    def test_it_raises_InvalidDeclarationError_with_called_with_non_lms_authority(
        self, command
    ):
        with pytest.raises(InvalidDeclarationError):
            BulkExecutor(sentinel.db).execute_batch(
                command.type, command.body.type, {}, [command]
            )

    @pytest.fixture
    def handler(self, patch, request):
        return patch(f"h.services.bulk_executor._executor.{request.param}")

    @pytest.fixture
    def commands(self):
        return [CommandFactory.user_upsert()]
