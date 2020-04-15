from copy import deepcopy
from operator import attrgetter

import pytest
from h_matchers import Any
from h_matchers.decorator import fluent_entrypoint
from h_matchers.matcher.core import Matcher

from h.h_api.bulk_api import Report
from h.h_api.exceptions import ConflictingDataError, UnsupportedOperationError
from h.models import User, UserIdentity
from h.services.bulk_executor._actions import UserUpsertAction
from tests.h.services.bulk_executor.conftest import upsert_user_command


# TODO! - Move this to h-matchers and test it
class AnyObject(Matcher):
    def __init__(self, class_=None, attributes=None):
        self.class_ = class_
        self.attributes = attributes
        super().__init__("dummy", self._matches_object)

    @fluent_entrypoint
    def of_class(self, class_):
        self.class_ = class_

        return self

    @fluent_entrypoint
    def with_attrs(self, attributes):
        self.attributes = attributes

        return self

    def _matches_object(self, other):
        if self.class_ is None:
            if not isinstance(other, object):
                return False

        elif self.class_ != type(other):
            return False

        if self.attributes is not None:
            for key, value in self.attributes.items():
                if not hasattr(other, key):
                    return False

                if getattr(other, key) != value:
                    return False

        return True

    def __getattr__(self, item):
        """Allow our attributes spec to be accessed as attributes."""

        if self.attributes is not None and item in self.attributes:
            return self.attributes[item]

        return super().__getattribute__(item)

    def __str__(self):
        extras = f" with attributes {self.attributes}" if self.attributes else ""

        return f"<Any instance of {self.class_} {extras}>"


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
        users = list(db_session.query(User).order_by(User.display_name))

        expected_users = sorted(
            [UserMatcher(command.body.attributes) for command in commands],
            key=attrgetter("display_name"),
        )

        assert users == expected_users

    @pytest.fixture
    def commands(self):
        return [upsert_user_command(i) for i in range(3)]
