from datetime import datetime, timedelta

from h_matchers import Any
from pytest import fixture

from h.sql_tasks.sql_query import SQLQuery


class TestSQLQuery:
    def test_execute(self, query, connection):
        self.assert_query_null_pre_execute(query)

        query.execute(connection)

        assert query.rows == [("value",)]
        assert query.columns == ["column"]
        self.assert_query_sets_dates_post_execute(query)

    def test_execute_with_a_query_returning_no_rows(self, query_no_rows, connection):
        self.assert_query_null_pre_execute(query_no_rows)

        query_no_rows.execute(connection)

        assert query_no_rows.rows is None
        assert query_no_rows.columns is None
        self.assert_query_sets_dates_post_execute(query_no_rows)

    def test_dump(self, query, connection):
        query.execute(connection)

        text = query.dump(indent=">>> ")
        # We're not going to assert everything about this. The exact formatting
        # doesn't matter. So this is more of a smoke test to show it's not
        # totally broken
        assert text.startswith(
            """>>> 0=> SELECT 'value' AS column
>>> +----------+
>>> | column   |
>>> |----------|
>>> | value    |
>>> +----------+"""
        )

    def test_dump_works_with_no_rows(self, query_no_rows):
        assert query_no_rows.dump()

    def assert_query_null_pre_execute(self, query):
        assert query.rows is None
        assert query.columns is None
        assert query.start_time is None
        assert query.duration is None

    def assert_query_sets_dates_post_execute(self, query):
        # These values are just FYI, so we'll take a shallow approach to
        # checking the values are correct
        assert query.start_time == Any.instance_of(datetime)
        assert (query.start_time - datetime.now()) < timedelta(seconds=1)
        assert query.duration == Any.instance_of(timedelta)
        assert query.duration <= timedelta(seconds=1)

    @fixture
    def connection(self, db_session):
        with db_session.bind.connect() as connection:
            yield connection

    @fixture
    def query(self):
        return SQLQuery(0, "SELECT 'value' AS column")

    @fixture
    def query_no_rows(self):
        return SQLQuery(0, 'ANALYZE "user"')
