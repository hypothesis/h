"""Individual actions for modifying the DB in bulk."""
from copy import deepcopy

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import ProgrammingError
from zope.sqlalchemy import mark_changed

from h.h_api.bulk_api import Report
from h.h_api.exceptions import (
    CommandSequenceError,
    ConflictingDataError,
    UnsupportedOperationError,
)
from h.models import Group, User, UserIdentity


class DBAction:
    """Base class for all DB actions.

    Provides an interface and a couple of useful methods.
    """

    def __init__(self, db):
        self.db = db

    def execute(self, batch, **kwargs):
        """Process a series of commands.

        The commands are assumed to be appropriate for this action type.
        """

        raise NotImplementedError()

    @staticmethod
    def _check_upsert_queries(batch, expected_keys):
        """Check that the query matches expectations and the attributes.

        :param batch: A collection of command objects
        :param expected_keys: The keys which must be in the query and match
                              the attributes with the same name.
        """

        for command in batch:
            query = command.body.query

            # This is technically overkill as the schema should make sure we
            # can't receive queries we aren't expecting
            if set(query.keys()) != set(expected_keys):
                raise UnsupportedOperationError(
                    f"Upserting by query fields '{query.keys()}' is not supported"
                )

            # Checking that the values are the same is a bit more important, as
            # this happens post schema, and could therefore be wrong
            for key, expected in query.items():
                if command.body.attributes[key] != expected:
                    raise UnsupportedOperationError(
                        "Upserting different values to the query is not supported. "
                        f"Different value found in key '{key}'"
                    )

    def _execute_statement(self, stmt):
        result = self.db.execute(stmt)

        # Let SQL Alchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(self.db)

        return result


class GroupUpsertAction(DBAction):
    """Perform a bulk group upsert."""

    def execute(self, batch, effective_user_id=None, **_):
        if effective_user_id is None:
            raise CommandSequenceError(
                "Effective user must be configured before upserting groups"
            )

        # Check that we can actually process this batch
        self._check_upsert_queries(
            batch, expected_keys=["authority", "authority_provided_id"]
        )

        # Prep the query
        values = [command.body.attributes for command in batch]
        for value in values:
            value["creator_id"] = effective_user_id

        stmt = insert(Group).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["authority", "authority_provided_id"],
            set_={"name": stmt.excluded.name},
        ).returning(Group.id, Group.authority, Group.authority_provided_id)

        # Upsert the data
        group_rows = self._execute_statement(stmt).fetchall()

        # Report back
        return [
            Report(
                id_,
                public_id=Group(
                    authority=authority, authority_provided_id=authority_provided_id
                ).groupid,
            )
            for id_, authority, authority_provided_id in group_rows
        ]


class UserUpsertAction(DBAction):
    """Perform a bulk user upsert.

    :raises ConflictingDataError: If two users attempt to use the same identity
    """

    def execute(self, batch, **_):
        # Check that we can actually process this batch
        self._check_upsert_queries(batch, expected_keys=["authority", "username"])

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
            Report(id_, public_id=User(authority=authority, _username=username).userid)
            for id_, authority, username in user_rows
        ]

    def _upsert_user_table(self, users):
        stmt = self._upsert_statement(
            User,
            users,
            index=[
                # The text wrapper here prevents SQLAlchemy from quoting the
                # string, and we need it to be verbatim
                text("lower(replace(username, '.'::text, ''::text)), authority")
            ],
            upsert=["display_name"],
        ).returning(User.id, User.authority, User._username)

        return self._execute_statement(stmt).fetchall()

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

            self._execute_statement(
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
