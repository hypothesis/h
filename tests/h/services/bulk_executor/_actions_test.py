from copy import deepcopy

import pytest
from h_matchers import Any

from h.h_api.bulk_api import Report
from h.h_api.exceptions import ConflictingDataError, UnsupportedOperationError
from h.models import User
from h.services.bulk_executor._actions import UserUpsertAction
from tests.h.services.bulk_executor.conftest import upsert_user_command


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
        return [upsert_user_command(i) for i in range(3)]
