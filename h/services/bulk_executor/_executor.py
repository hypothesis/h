"""Bulk executor for use with h.h_api.bulk_api."""

from sqlalchemy.orm.exc import NoResultFound

from h.h_api.bulk_api.executor import Executor
from h.h_api.enums import CommandType, DataType
from h.h_api.exceptions import InvalidDeclarationError, UnsupportedOperationError
from h.models import User
from h.services.bulk_executor._actions import (
    GroupMembershipCreateAction,
    GroupUpsertAction,
    UserUpsertAction,
)


class BulkExecutor(Executor):
    """Executor of command objects which will modify the database in bulk."""

    def __init__(self, db, authority="lms.hypothes.is"):
        """
        :param db: DB session object
        :param authority: Restrict all request to this authority
        """
        self.db = db
        self.authority = authority

        self.handlers = {
            (CommandType.UPSERT, DataType.USER): UserUpsertAction(self.db),
            (CommandType.UPSERT, DataType.GROUP): GroupUpsertAction(self.db),
            (
                CommandType.CREATE,
                DataType.GROUP_MEMBERSHIP,
            ): GroupMembershipCreateAction(self.db),
        }

        self.effective_user_id = None

    def configure(self, config):
        """Process a configuration instruction."""
        self._assert_authority("effective user", config.effective_user, embedded=True)

        try:
            user = (
                self.db.query(User).filter(User.userid == config.effective_user).one()
            )

        except NoResultFound:
            raise InvalidDeclarationError(
                f"No user found for effective user: '{config.effective_user}'"
            )

        self.effective_user_id = user.id

    def execute_batch(self, command_type, data_type, default_config, batch):
        """Execute a batch of instructions of the same type."""

        # Check the commands for the correct authority
        for command in batch:
            if data_type in (DataType.USER, DataType.GROUP):
                self._assert_authority(
                    "authority", command.body.attributes["authority"]
                )
                self._assert_authority(
                    "query authority", command.body.query["authority"]
                )

        # Get a handler for this action
        handler = self.handlers.get((command_type, data_type), None)

        if handler is None:
            raise UnsupportedOperationError(
                f"No implementation for {command_type.value} {data_type.value}"
            )

        # Do it
        return handler.execute(
            batch, effective_user_id=self.effective_user_id, **default_config
        )

    def _assert_authority(self, field, value, embedded=False):
        if embedded and value.endswith(f"@{self.authority}"):
            return

        if value == self.authority:
            return

        raise InvalidDeclarationError(
            f"The {field} '{value}' does not match the expected authority"
        )
