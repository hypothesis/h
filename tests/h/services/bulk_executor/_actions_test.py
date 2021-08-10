from copy import deepcopy
from operator import attrgetter
from unittest.mock import Mock, patch, sentinel

import pytest
from h_api.bulk_api import Report
from h_api.exceptions import (
    CommandSequenceError,
    ConflictingDataError,
    UnsupportedOperationError,
)
from h_matchers import Any
from h_matchers.matcher.object import AnyObject
from sqlalchemy.exc import IntegrityError, ProgrammingError

from h.models import Group, GroupMembership, User, UserIdentity
from h.models.group import PRIVATE_GROUP_TYPE_FLAGS
from h.services.bulk_executor._actions import (
    GroupMembershipCreateAction,
    GroupUpsertAction,
    UserUpsertAction,
)
from tests.h.services.bulk_executor.conftest import (
    AUTHORITY,
    group_membership_create,
    group_upsert_command,
    upsert_user_command,
)


class UserMatcher(AnyObject):
    def __init__(self, attributes):
        attributes["identities"] = [
            AnyObject(UserIdentity, identity) for identity in attributes["identities"]
        ]

        super().__init__(User, attributes)


class TestBulkUserUpsert:
    def test_it_can_insert_new_records(self, db_session, commands):
        reports = UserUpsertAction(db_session).execute(commands)

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_users_match_commands(db_session, commands)

    def test_it_can_update_records(self, db_session, commands):
        update_commands = [
            upsert_user_command(i, display_name=f"changed_{i}") for i in range(3)
        ]

        action = UserUpsertAction(db_session)
        action.execute(commands)
        reports = action.execute(update_commands)

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_users_match_commands(db_session, update_commands)

    def test_if_tails_with_duplicate_identities(self, db_session):
        command_1 = upsert_user_command(1)
        command_2 = upsert_user_command(2)
        commands = [command_1, command_2]

        command_2.body.attributes["identities"] = command_1.body.attributes[
            "identities"
        ]

        with pytest.raises(ConflictingDataError):
            UserUpsertAction(db_session).execute(commands)

    def test_other_db_errors_are_raised_directly(self, db_session, programming_error):
        action = UserUpsertAction(db_session)

        fake_execute_result = Mock(spec_set=["fetchall"])
        fake_execute_result.fetchall.return_value = [["id", "authority", "username"]]

        with patch.object(action, "_execute_statement") as _execute_statement:
            # We need the second call to fail during _upsert_identities
            _execute_statement.side_effect = [fake_execute_result, programming_error]

            with pytest.raises(ProgrammingError):
                action.execute([upsert_user_command(0)])

    def test_it_returns_in_the_same_order_as_the_commands(self, db_session, commands):
        # Insert the values to set db order, then update them in reverse
        action = UserUpsertAction(db_session)
        reports = action.execute(commands)
        reversed_reports = action.execute(list(reversed(deepcopy(commands))))

        ids = [report.id for report in reports]
        reversed_ids = [report.id for report in reversed_reports]

        assert reversed_ids == list(reversed(ids))

    @pytest.mark.parametrize("field", ["username", "authority"])
    def test_it_fails_with_mismatched_queries(self, db_session, field):
        command = upsert_user_command(**{field: "value"})
        command.body.query[field] = "DIFFERENT"

        with pytest.raises(UnsupportedOperationError):
            UserUpsertAction(db_session).execute([command])

    def test_if_fails_with_unsupported_queries(self, db_session):
        command = upsert_user_command()
        command.body.query["something_new"] = "foo"

        with pytest.raises(UnsupportedOperationError):
            UserUpsertAction(db_session).execute([command])

    @staticmethod
    def assert_users_match_commands(db_session, commands):
        users = list(db_session.query(User).order_by(User.display_name))

        expected_users = sorted(
            [UserMatcher(command.body.attributes) for command in commands],
            key=attrgetter("display_name"),
        )

        assert users == expected_users

    @pytest.fixture
    def commands(self):
        return [upsert_user_command(i) for i in range(3)]


class TestBulkGroupUpsert:
    def test_it_can_insert_new_records(self, db_session, commands, user):
        reports = GroupUpsertAction(db_session).execute(
            commands, effective_user_id=user.id
        )

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_groups_match_commands(db_session, commands)
        self.assert_groups_are_private_and_owned_by_user(db_session, user)

    def test_it_can_update_records(self, db_session, commands, user):
        update_commands = [
            group_upsert_command(i, name=f"changed_{i}") for i in range(3)
        ]

        GroupUpsertAction(db_session).execute(commands, effective_user_id=user.id)
        reports = GroupUpsertAction(db_session).execute(
            update_commands, effective_user_id=user.id
        )

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_groups_match_commands(db_session, update_commands)
        self.assert_groups_are_private_and_owned_by_user(db_session, user)

    def test_it_returns_in_the_same_order_as_the_commands(
        self, db_session, commands, user
    ):
        # Insert the values to set db order, then update them in reverse
        action = GroupUpsertAction(db_session)
        reports = action.execute(commands, effective_user_id=user.id)
        reversed_reports = action.execute(
            list(reversed(deepcopy(commands))), effective_user_id=user.id
        )

        ids = [report.id for report in reports]
        reversed_ids = [report.id for report in reversed_reports]

        assert reversed_ids == list(reversed(ids))

    def test_it_fails_with_no_effective_user(self, db_session):
        with pytest.raises(CommandSequenceError):
            GroupUpsertAction(db_session).execute(
                sentinel.batch, effective_user_id=None
            )

    def test_it_fails_with_duplicate_groups(self, db_session, user):
        command = group_upsert_command(0)

        with pytest.raises(ConflictingDataError):
            GroupUpsertAction(db_session).execute(
                [command, command], effective_user_id=user.id
            )

    def test_other_db_errors_are_raised_directly(
        self, db_session, user, programming_error
    ):
        action = GroupUpsertAction(db_session)
        with patch.object(action, "_execute_statement") as _execute_statement:
            _execute_statement.side_effect = programming_error

            with pytest.raises(ProgrammingError):
                action.execute([group_upsert_command(0)], effective_user_id=user.id)

    @pytest.mark.parametrize("field", ["authority", "authority_provided_id"])
    def test_it_fails_with_mismatched_queries(self, db_session, field, user):
        command = group_upsert_command(**{field: "value"})
        command.body.query[field] = "DIFFERENT"

        with pytest.raises(UnsupportedOperationError):
            GroupUpsertAction(db_session).execute([command], effective_user_id=user.id)

    def test_if_fails_with_unsupported_queries(self, db_session, user):
        command = group_upsert_command()
        command.body.query["something_new"] = "foo"

        with pytest.raises(UnsupportedOperationError):
            GroupUpsertAction(db_session).execute([command], effective_user_id=user.id)

    @staticmethod
    def assert_groups_are_private_and_owned_by_user(db_session, user):
        groups = list(db_session.query(Group).filter(Group.authority == AUTHORITY))

        for group in groups:
            # Check the groups are private
            assert group.joinable_by == PRIVATE_GROUP_TYPE_FLAGS.joinable_by
            assert group.readable_by == PRIVATE_GROUP_TYPE_FLAGS.readable_by
            assert group.writeable_by == PRIVATE_GROUP_TYPE_FLAGS.writeable_by

            # Check they are owned by
            assert group.creator_id == user.id

    @staticmethod
    def assert_groups_match_commands(db_session, commands):
        groups = list(
            db_session.query(Group)
            .filter(Group.authority == AUTHORITY)
            .order_by(Group.name)
        )

        expected_groups = sorted(
            [
                AnyObject.of_type(Group).with_attrs(command.body.attributes)
                for command in commands
            ],
            key=attrgetter("name"),
        )

        assert groups == expected_groups

    @pytest.fixture
    def commands(self):
        return [group_upsert_command(i) for i in range(3)]


class TestBulkGroupMembershipCreate:
    def test_it_can_insert_new_records(self, db_session, commands):
        reports = GroupMembershipCreateAction(db_session).execute(commands)

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_membership_matches_commands(db_session, commands)

    def test_it_can_continue_with_existing_records(self, db_session, commands):
        GroupMembershipCreateAction(db_session).execute(commands)
        reports = GroupMembershipCreateAction(db_session).execute(
            commands, on_duplicate="continue"
        )

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_membership_matches_commands(db_session, commands)

    def test_it_fails_without_continue(self, db_session, commands):
        with pytest.raises(UnsupportedOperationError):
            GroupMembershipCreateAction(db_session).execute(
                commands, on_duplicate="fail"
            )

    def test_the_reports_match_the_command_order(self, db_session, commands):
        initial_reports = GroupMembershipCreateAction(db_session).execute(commands)
        initial_ids = [report.id for report in initial_reports]

        reports = GroupMembershipCreateAction(db_session).execute(
            list(reversed(commands))
        )
        final_ids = [report.id for report in reports]

        assert final_ids == list(reversed(initial_ids))

    def test_it_raises_conflict_with_bad_user_foreign_key(self, db_session, groups):
        with pytest.raises(ConflictingDataError):
            GroupMembershipCreateAction(db_session).execute(
                [group_membership_create(99999, groups[0].id)]
            )

    def test_it_raises_conflict_with_bad_group_foreign_key(self, db_session, user):
        with pytest.raises(ConflictingDataError):
            GroupMembershipCreateAction(db_session).execute(
                [group_membership_create(user.id, 999999)]
            )

    def test_other_db_errors_are_raised_directly(self, db_session, integrity_error):
        action = GroupMembershipCreateAction(db_session)
        with patch.object(action, "_execute_statement") as _execute_statement:
            _execute_statement.side_effect = integrity_error

            with pytest.raises(IntegrityError):
                action.execute([group_membership_create(1, 2)])

    @staticmethod
    def assert_membership_matches_commands(db_session, commands):
        # Sort by `group_id` as these tests always use the same `user_id`
        memberships = list(
            db_session.query(GroupMembership).order_by(GroupMembership.group_id)
        )

        expected_memberships = sorted(
            [
                AnyObject.of_type(GroupMembership).with_attrs(
                    {
                        "user_id": command.body.member.id,
                        "group_id": command.body.group.id,
                    }
                )
                for command in commands
            ],
            key=attrgetter("group_id"),
        )

        assert memberships == expected_memberships

    @pytest.fixture
    def commands(self, user, groups):
        return [group_membership_create(user.id, group.id) for group in groups]

    @pytest.fixture
    def groups(self, db_session, user):
        groups = [
            Group(
                name=f"group_{i}",
                authority=user.authority,
                authority_provided_id=f"ap_id_{i}",
            )
            for i in range(3)
        ]

        db_session.add_all(groups)
        db_session.flush()

        return groups


@pytest.fixture
def programming_error():
    return ProgrammingError("statement", "params", orig=Mock())


@pytest.fixture
def integrity_error():
    return IntegrityError("statement", "params", orig=Mock())
