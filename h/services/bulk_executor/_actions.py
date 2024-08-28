"""Individual actions for modifying the DB in bulk."""

from copy import deepcopy

from h_api.bulk_api import Report
from h_api.exceptions import (
    CommandSequenceError,
    ConflictingDataError,
    UnsupportedOperationError,
)
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, ProgrammingError
from zope.sqlalchemy import mark_changed

from h.models import Group, GroupMembership, User, UserIdentity
from h.models.group import GROUP_TYPE_FLAGS


class DBAction:
    """
    Base class for all DB actions.

    Provides an interface and a couple of useful methods.
    """

    def __init__(self, db):
        self.db = db

    def execute(self, batch, **kwargs):
        """
        Process a series of commands.

        The commands are assumed to be appropriate for this action type.
        """

        raise NotImplementedError()  # pragma: no cover

    @staticmethod
    def _check_upsert_queries(batch, expected_keys):
        """
        Validate the query for each command in `batch`.

        This method allows you to assert that:

         * Only the expected fields are present in the query
         * The value in the query matches the value in the attributes

        Our current upserting method requires the values we create to conflict
        with existing records to work. Therefore if we can't try to update with
        different values than those we create with. The methods are also
        hard coded to expect certain values which we can mandate here.

        :param batch: A collection of command objects
        :param expected_keys: The list of valid keys that are allowed in
                              command queries

        :raise UnsupportedOperationError: if any of the conditions above are
                                          not satisfied
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

        # Let SQLAlchemy know that something has changed, otherwise it will
        # never commit the transaction we are working on and it will get rolled
        # back
        mark_changed(self.db)

        return result


class GroupUpsertAction(DBAction):
    """Perform a bulk group upsert."""

    type_flags = GROUP_TYPE_FLAGS["private"]

    def execute(self, batch, effective_user_id=None, **_):
        if effective_user_id is None:
            raise CommandSequenceError(
                "Effective user must be configured before upserting groups"
            )

        # Check that we can actually process this batch
        self._check_upsert_queries(
            batch, expected_keys=["authority", "authority_provided_id"]
        )

        static_values = {
            # Set the group to be owned by the effective user
            "creator_id": effective_user_id,
            # Set the group to match the specified type (private in this case)
            "joinable_by": self.type_flags.joinable_by,
            "readable_by": self.type_flags.readable_by,
            "writeable_by": self.type_flags.writeable_by,
        }

        # Prep the query
        values = [command.body.attributes for command in batch]
        for value in values:
            value.update(static_values)

        stmt = insert(Group).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["authority", "authority_provided_id"],
            set_={"name": stmt.excluded.name},
        ).returning(Group.id, Group.authority, Group.authority_provided_id)

        # Upsert the data
        try:
            group_rows = self._execute_statement(stmt).fetchall()

        except ProgrammingError as err:
            # https://www.postgresql.org/docs/9.4/errcodes-appendix.html
            # 21000 == cardinality violation
            if err.orig.pgcode == "21000":
                raise ConflictingDataError(
                    "Attempted to create two groups with the same authority and id"
                ) from err

            raise

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


class GroupMembershipCreateAction(DBAction):
    """
    Perform a bulk group membership create.

    :raises ConflictingDataError: Upon trying to create a membership to a user
                                  or group that does not exist
    """

    def execute(self, batch, on_duplicate="continue", **_):
        """
        Execute GroupMembershipCreateAction.

        :param on_duplicate: Specify behavior when a record already exists. The
                             default is "continue"
        """
        if on_duplicate != "continue":
            raise UnsupportedOperationError(
                "Create modes other than 'continue' have not been implemented"
            )

        values = [
            {"user_id": command.body.member.id, "group_id": command.body.group.id}
            for command in batch
        ]

        stmt = insert(GroupMembership).values(values)

        # This update doesn't change the row, but it does count as it being
        # 'updated' which means we can get the values in the "RETURNING"
        # clause and do the select in one go
        stmt = stmt.on_conflict_do_update(
            index_elements=["user_id", "group_id"],
            set_={"user_id": stmt.excluded.user_id},
        )

        stmt = stmt.returning(GroupMembership.id)

        try:
            membership_rows = self._execute_statement(stmt).fetchall()

        except IntegrityError as err:
            # https://www.postgresql.org/docs/9.1/errcodes-appendix.html
            # 23503 = foreign_key_violation
            if err.orig.pgcode == "23503":
                raise ConflictingDataError(
                    "Cannot insert group membership as either the user or "
                    f"group specified does not exist: {err.params}"
                ) from err

            raise

        return [Report(id_) for (id_,) in membership_rows]


class UserUpsertAction(DBAction):
    """
    Perform a bulk user upsert.

    :raise ConflictingDataError: If two users attempt to use the same identity
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
        ).returning(
            User.id, User.authority, User._username  # pylint: disable=protected-access
        )

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
                ) from err

            raise

    @staticmethod
    def _upsert_statement(table, values, index, upsert):
        stmt = insert(table).values(values)

        return stmt.on_conflict_do_update(
            index_elements=index,
            set_={field: getattr(stmt.excluded, field) for field in upsert},
        )
