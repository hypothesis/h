from copy import deepcopy
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.h_api.bulk_api import Report
from h.h_api.exceptions import (
    CommandSequenceError,
    ConflictingDataError,
    UnsupportedOperationError,
)
from h.models import Group, GroupMembership, User
from h.services.bulk_executor._actions import (
    GroupMembershipCreateAction,
    GroupUpsertAction,
    UserUpsertAction,
)
from tests.h.services.bulk_executor.conftest import CommandFactory


def assert_models_match_data(models_by_name, attrs_by_name, handlers=None):
    assert set(models_by_name.keys()) == set(attrs_by_name.keys())

    for name, model in models_by_name.items():
        expected_attrs = attrs_by_name[name]

        for field, value in expected_attrs.items():
            found = getattr(model, field)

            if handlers and field in handlers:
                found = handlers[field](found)

            assert found == value


class TestBulkUserUpsert:
    def test_it_can_insert_new_records(self, db_session, commands):
        reports = UserUpsertAction(db_session).execute(commands)

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_users_match_commands(db_session, commands)

    def test_it_can_update_records(self, db_session, commands):
        update_commands = [
            CommandFactory.user_upsert(i, extras={"display_name": f"changed_{i}"})
            for i in range(3)
        ]

        action = UserUpsertAction(db_session)
        action.execute(commands)
        reports = action.execute(update_commands)

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_users_match_commands(db_session, update_commands)

    def test_if_tails_with_duplicate_identities(self, db_session):
        command_1 = CommandFactory.user_upsert(1)
        command_2 = CommandFactory.user_upsert(2)
        commands = [command_1, command_2]

        command_2.body.attributes["identities"] = command_1.body.attributes[
            "identities"
        ]

        with pytest.raises(ConflictingDataError):
            UserUpsertAction(db_session).execute(commands)

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
        command = CommandFactory.user_upsert(extras={field: "value"})
        command.body.query[field] = "DIFFERENT"

        with pytest.raises(UnsupportedOperationError):
            UserUpsertAction(db_session).execute([command])

    def test_if_fails_with_unsupported_queries(self, db_session):
        command = CommandFactory.user_upsert()
        command.body.query["something_new"] = "foo"

        with pytest.raises(UnsupportedOperationError):
            UserUpsertAction(db_session).execute([command])

    def assert_users_match_commands(self, db_session, commands):
        attrs_by_name = {
            command.body.attributes["username"]: command.body.attributes
            for command in commands
        }

        models_by_name = {user.username: user for user in db_session.query(User)}

        assert_models_match_data(
            models_by_name,
            attrs_by_name,
            {
                "identities": lambda found: [
                    {
                        "provider": identity.provider,
                        "provider_unique_id": identity.provider_unique_id,
                    }
                    for identity in found
                ]
            },
        )

    @pytest.fixture
    def commands(self):
        return [CommandFactory.user_upsert(i) for i in range(3)]


class TestBulkGroupUpsert:
    def test_it_can_insert_new_records(self, db_session, commands, user):
        reports = GroupUpsertAction(db_session).execute(
            commands, effective_user_id=user.id
        )

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_groups_match_commands(db_session, commands)

    def test_it_can_update_records(self, db_session, commands, user):
        update_commands = [
            CommandFactory.group_upsert(i, extras={"name": f"changed_{i}"})
            for i in range(3)
        ]

        GroupUpsertAction(db_session).execute(commands, effective_user_id=user.id)
        reports = GroupUpsertAction(db_session).execute(
            update_commands, effective_user_id=user.id
        )

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_groups_match_commands(db_session, update_commands)

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

    @pytest.mark.parametrize("field", ["authority", "authority_provided_id"])
    def test_it_fails_with_mismatched_queries(self, db_session, field, user):
        command = CommandFactory.group_upsert(extras={field: "value"})
        command.body.query[field] = "DIFFERENT"

        with pytest.raises(UnsupportedOperationError):
            GroupUpsertAction(db_session).execute([command], effective_user_id=user.id)

    def test_if_fails_with_unsupported_queries(self, db_session, user):
        command = CommandFactory.group_upsert()
        command.body.query["something_new"] = "foo"

        with pytest.raises(UnsupportedOperationError):
            GroupUpsertAction(db_session).execute([command], effective_user_id=user.id)

    def assert_groups_match_commands(self, db_session, commands):
        attrs_by_name = {
            command.body.attributes["name"]: command.body.attributes
            for command in commands
        }

        models_by_name = {
            group.name: group
            for group in db_session.query(Group).filter(
                Group.authority == CommandFactory.AUTHORITY
            )
        }

        assert_models_match_data(models_by_name, attrs_by_name)

    @pytest.fixture
    def commands(self):
        return [CommandFactory.group_upsert(i) for i in range(3)]


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
                [CommandFactory.group_membership_create(99999, groups[0].id)]
            )

    def test_it_raises_conflict_with_bad_group_foreign_key(self, db_session, user):
        with pytest.raises(ConflictingDataError):
            GroupMembershipCreateAction(db_session).execute(
                [CommandFactory.group_membership_create(user.id, 999999)]
            )

    @pytest.mark.xfail
    def test_it_fails_with_mismatched_queries(self):
        raise NotImplementedError()

    @pytest.mark.xfail
    def test_if_fails_with_unsupported_queries(self):
        raise NotImplementedError()

    def assert_membership_matches_commands(self, db_session, commands):
        rel_tuples = [
            (rel.user_id, rel.group_id) for rel in db_session.query(GroupMembership)
        ]
        command_tuples = [
            (command.body.member.id, command.body.group.id) for command in commands
        ]

        assert rel_tuples == command_tuples

    @pytest.fixture
    def commands(self, db_session, user, groups):
        return [
            CommandFactory.group_membership_create(user.id, group.id)
            for group in groups
        ]

    @pytest.fixture
    def groups(self, db_session):
        groups = [
            Group(
                name=f"group_{i}",
                authority="lms.hypothes.is",
                authority_provided_id=f"ap_id_{i}",
            )
            for i in range(3)
        ]

        db_session.add_all(groups)
        db_session.flush()

        return groups
