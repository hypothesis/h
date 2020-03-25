from unittest.mock import sentinel

import pytest
from pytest import param

from h.h_api.bulk_api.model.config_body import Configuration
from h.h_api.enums import CommandType, DataType
from h.h_api.exceptions import InvalidDeclarationError
from h.services.bulk_executor.executors import AuthorityCheckingExecutor, DBExecutor
from tests.h.services.bulk_executor.conftest import CommandFactory


class TestDBExecutor:
    def test_it_calls_bulk_user_upsert(self, db_session, BulkUserUpsert):
        DBExecutor(db_session).execute_batch(
            CommandType.UPSERT, DataType.USER, sentinel.config, sentinel.user_commands
        )

        BulkUserUpsert.assert_called_once_with(db_session)
        bulk_upsert = BulkUserUpsert.return_value
        bulk_upsert.upsert_users.assert_called_once_with(sentinel.user_commands)

    @pytest.fixture(autouse=True)
    def BulkUserUpsert(self, patch):
        return patch("h.services.bulk_executor.executors.BulkUserUpsert")


class TestAuthorityCheckingExecutor:
    def test_it_raises_InvalidDeclarationError_with_non_lms_authority(self):
        config = Configuration.create(
            effective_user="acct:user@bad_authority.com", total_instructions=2
        )

        with pytest.raises(InvalidDeclarationError):
            AuthorityCheckingExecutor(sentinel.db).configure(config)

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
            AuthorityCheckingExecutor(sentinel.db).execute_batch(
                command.type, command.body.type, {}, [command]
            )

    @pytest.fixture(autouse=True)
    def DBExecutor(self, patch):
        return patch("h.services.bulk_executor.executors.DBExecutor")
