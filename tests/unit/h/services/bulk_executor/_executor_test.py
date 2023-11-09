import pytest
from h_api.bulk_api.model.config_body import Configuration
from h_api.enums import CommandType, DataType
from h_api.exceptions import InvalidDeclarationError, UnsupportedOperationError
from pytest import param

from h.services.bulk_executor._executor import BulkExecutor
from tests.unit.h.services.bulk_executor.conftest import (
    AUTHORITY,
    group_upsert_command,
    upsert_user_command,
)


class TestDBExecutor:
    @pytest.mark.parametrize(
        "command_type,data_type,handler",
        (
            (CommandType.UPSERT, DataType.USER, "UserUpsertAction"),
            (CommandType.UPSERT, DataType.GROUP, "GroupUpsertAction"),
            (
                CommandType.CREATE,
                DataType.GROUP_MEMBERSHIP,
                "GroupMembershipCreateAction",
            ),
        ),
        indirect=["handler"],
    )
    def test_it_calls_correct_db_handler(
        self, db_session, command_type, data_type, handler, commands
    ):
        executor = BulkExecutor(db_session, authority=AUTHORITY)
        handler.assert_called_once_with(db_session)

        executor.effective_user_id = 1

        # These commands aren't actually the right type, but it doesn't
        # matter for this test
        executor.execute_batch(command_type, data_type, {"config_option": 2}, commands)

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
        executor = BulkExecutor(db_session, authority=AUTHORITY)

        with pytest.raises(UnsupportedOperationError):
            executor.execute_batch(command_type, data_type, commands, {})

    def test_it_raises_InvalidDeclarationError_with_non_lms_authority(self, executor):
        config = Configuration.create(
            effective_user="acct:user@bad_authority.com", total_instructions=2
        )

        with pytest.raises(InvalidDeclarationError):
            executor.configure(config)

    @pytest.mark.parametrize(
        "command",
        (
            param(
                upsert_user_command(authority="bad"),
                id="User: bad authority in attributes",
            ),
            param(
                upsert_user_command(query_authority="bad"),
                id="User: bad authority in query",
            ),
            param(
                group_upsert_command(authority="bad"),
                id="Group: bad authority in attributes",
            ),
            param(
                group_upsert_command(query_authority="bad"),
                id="User: bad authority in query",
            ),
        ),
    )
    def test_it_raises_InvalidDeclarationError_with_called_with_non_lms_authority(
        self, command, executor
    ):
        with pytest.raises(InvalidDeclarationError):
            executor.execute_batch(command.type, command.body.type, {}, [command])

    def test_configure_looks_up_the_effective_user(self, executor, user):
        assert executor.effective_user_id is None

        executor.configure(
            Configuration.create(effective_user=user.userid, total_instructions=2)
        )

        assert executor.effective_user_id == user.id

    def test_configure_raises_if_the_effective_user_does_not_exist(self, executor):
        with pytest.raises(InvalidDeclarationError):
            executor.configure(
                Configuration.create(
                    effective_user=f"acct:missing@{AUTHORITY}", total_instructions=2
                )
            )

    @pytest.fixture
    def executor(self, db_session):
        return BulkExecutor(db_session, authority=AUTHORITY)

    @pytest.fixture
    def handler(self, patch, request):
        return patch(f"h.services.bulk_executor._executor.{request.param}")

    @pytest.fixture
    def commands(self):
        return [group_upsert_command(authority=AUTHORITY)]
