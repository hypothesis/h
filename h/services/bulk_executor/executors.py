from h.h_api.bulk_api.executor import AutomaticReportExecutor
from h.h_api.enums import CommandType, DataType
from h.h_api.exceptions import InvalidDeclarationError
from h.services.bulk_executor.bulk_user import BulkUserUpsert


class DBExecutor(AutomaticReportExecutor):
    def __init__(self, db):
        self.db = db
        self.effective_user = None

    def configure(self, config):
        self.effective_user = config.effective_user

    def execute_batch(self, command_type, data_type, default_config, batch):
        if data_type == DataType.USER and command_type == CommandType.UPSERT:
            return BulkUserUpsert(self.db).upsert_users(batch)

        return super().execute_batch(command_type, data_type, default_config, batch)


class AuthorityCheckingExecutor(DBExecutor):
    """A bulk executor which checks the authority."""

    def __init__(self, db, authority="lms.hypothes.is"):
        self.authority = authority

        super().__init__(db)

    def configure(self, config):
        self._assert_authority("effective user", config.effective_user, embedded=True)

        super().configure(config)

    def execute_batch(self, command_type, data_type, default_config, batch):
        for command in batch:
            self._check_authority(data_type, command.body)

        return super().execute_batch(command_type, data_type, default_config, batch)

    def _assert_authority(self, field, value, embedded=False):
        if embedded and value.endswith(f"@{self.authority}"):
            return

        if value == self.authority:
            return

        raise InvalidDeclarationError(
            f"The {field} '{value}' does not match the expected authority"
        )

    def _check_authority(self, data_type, body):
        if data_type in (DataType.USER, DataType.GROUP):
            self._assert_authority("authority", body.attributes["authority"])
            self._assert_authority("query authority", body.query["authority"])
