"""Service for creating Executor objects to carry out bulk operations."""
from copy import deepcopy

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import ProgrammingError

from h.h_api.bulk_api import Report
from h.h_api.exceptions import ConflictingDataError
from h.models import UserIdentity
from h.models.user import User


class IndexLiteral:
    def __init__(self, string):
        self.string = string

    def _compiler_dispatch(self, *_, **__):
        return self.string


class BulkUserUpsert:
    def __init__(self, db):
        self.db = db

    def upsert_users(self, batch):
        # Split users and their embedded identity lists
        users, identities = [], []

        for command in batch:
            attributes = deepcopy(command.body.attributes)

            identities.append(attributes.pop("identities"))
            users.append(attributes)

        # Upsert the data
        user_rows = self._upsert_user_table(users)
        self._upsert_identities(identities, user_ids=[row[0] for row in user_rows])

        # Report back
        return [
            Report(
                Report.CommandResult.UPSERTED,
                User(authority=authority, _username=username).userid,
            )
            for _, authority, username in user_rows
        ]

    def _upsert_user_table(self, users):
        index = IndexLiteral("lower(replace(username, '.'::text, ''::text)), authority")

        stmt = self._upsert_statement(
            User, users, index=[index], upsert=["display_name"],
        ).returning(User.id, User.authority, User._username)

        return self.db.execute(stmt).fetchall()

    def _upsert_identities(self, identities, user_ids):
        flat_identities = []

        # Flatten the nested lists into a single list with user ids
        for id_, identity_list in zip(user_ids, identities):
            for identity in identity_list:
                identity["user_id"] = id_
                flat_identities.append(identity)

        try:
            # We can't tell the difference between a constraint violation
            # because the row we are trying to insert already exists, and
            # because the identity belongs to another user.
            # To get around this we attempt to 'upsert' after the conflict. If
            # the values match, nothing happens. If they are different a
            # cardinality violation is raised by Postgres.

            self.db.execute(
                self._upsert_statement(
                    UserIdentity,
                    flat_identities,
                    index=["provider", "provider_unique_id"],
                    upsert=["user_id"],
                ).returning(UserIdentity.id)
            )

        except ProgrammingError as err:
            # https://www.postgresql.org/docs/9.4/errcodes-appendix.html
            # 21000 == cardinality violation
            # This indicates the identity belongs to another user
            if err.orig.pgcode == "21000":
                raise ConflictingDataError(
                    "Attempted to assign existing identity to a different user"
                )

            raise

    @staticmethod
    def _upsert_statement(table, values, index, upsert):
        stmt = insert(table).values(values)

        return stmt.on_conflict_do_update(
            index_elements=index,
            set_={field: getattr(stmt.excluded, field) for field in upsert},
        )
