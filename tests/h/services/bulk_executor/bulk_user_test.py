import pytest
from h_matchers import Any

from h.h_api.bulk_api import Report
from h.h_api.exceptions import ConflictingDataError
from h.models import User
from h.services.bulk_executor.bulk_user import BulkUserUpsert
from tests.h.services.bulk_executor.conftest import CommandFactory


class TestBulkUserUpsert:
    def test_it_can_insert_new_records(self, db_session, commands):
        reports = BulkUserUpsert(db_session).upsert_users(commands)

        assert reports == Any.iterable.comprised_of(Any.instance_of(Report)).of_size(3)

        self.assert_users_match_commands(db_session, commands)

    def test_it_can_update_records(self, db_session, commands):
        update_commands = [
            CommandFactory.user_upsert(i, extras={"display_name": f"changed_{i}"})
            for i in range(3)
        ]

        BulkUserUpsert(db_session).upsert_users(commands)
        reports = BulkUserUpsert(db_session).upsert_users(update_commands)

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
            BulkUserUpsert(db_session).upsert_users(commands)

    @pytest.fixture
    def commands(self):
        return [CommandFactory.user_upsert(i) for i in range(3)]

    def user_id(self, user_command):
        query = user_command.body.query

        return f'acct:{query["username"]}@{query["authority"]}'

    def assert_users_match_commands(self, db_session, commands):
        attrs_by_userid = {
            self.user_id(command): command.body.attributes for command in commands
        }

        users_by_userid = {user.userid: user for user in db_session.query(User)}

        assert list(users_by_userid.keys()) == list(attrs_by_userid.keys())

        for user_id, user in users_by_userid.items():
            expected_attrs = attrs_by_userid[user_id]

            for field, value in expected_attrs.items():
                found = getattr(user, field)
                if field == "identities":
                    found = [
                        {
                            "provider": identity.provider,
                            "provider_unique_id": identity.provider_unique_id,
                        }
                        for identity in found
                    ]

                assert found == value
