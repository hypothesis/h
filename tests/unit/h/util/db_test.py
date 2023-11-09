import random
from unittest import mock

import pytest

from h.util.db import lru_cache_in_transaction, on_transaction_end


class TestLRUCacheInTransaction:
    def test_caches_during_transaction(self, db_session, mock_transaction):
        # Return values should be cached during the transaction, and the cache
        # cleared when the transaction ends.

        @lru_cache_in_transaction(db_session)
        def random_float(*args, **kwargs):  # pylint:disable=unused-argument
            return random.random()

        a = random_float("a")
        b = random_float("b")
        c = random_float("c", with_keywords=True)

        assert random_float("a") == a
        assert random_float("b") == b
        assert random_float("c", with_keywords=True) == c

        db_session.dispatch.after_transaction_end(db_session, mock_transaction)

        assert random_float("a") != a
        assert random_float("b") != b
        assert random_float("c", with_keywords=True) != c

    def test_cache_not_cleared_for_nested_transaction(
        self, db_session, mock_transaction
    ):
        """The cache should not be cleared when a nested transaction ends."""

        @lru_cache_in_transaction(db_session)
        def random_float(*args, **kwargs):  # pylint:disable=unused-argument
            return random.random()

        a = random_float("a")
        b = random_float("b")
        c = random_float("c", with_keywords=True)

        assert random_float("a") == a
        assert random_float("b") == b
        assert random_float("c", with_keywords=True) == c

        type(mock_transaction).parent = mock.PropertyMock(
            return_value=mock.Mock(spec=db_session.transaction)
        )
        db_session.dispatch.after_transaction_end(db_session, mock_transaction)

        assert random_float("a") == a
        assert random_float("b") == b
        assert random_float("c", with_keywords=True) == c


class TestOnTransactionEnd:
    def test_calls_wrapped_function_when_parent_transaction(
        self, db_session, mock_transaction
    ):
        spy = mock.Mock()

        @on_transaction_end(db_session)
        def transaction_ended():
            spy()

        db_session.dispatch.after_transaction_end(db_session, mock_transaction)

        spy.assert_called_once_with()

    def test_skips_wrapped_function_when_nested_transaction(
        self, db_session, mock_transaction
    ):
        spy = mock.Mock()
        type(mock_transaction).parent = mock.PropertyMock(
            return_value=mock.Mock(spec=db_session.transaction)
        )

        @on_transaction_end(db_session)
        def transaction_ended():
            spy()

        db_session.dispatch.after_transaction_end(db_session, mock_transaction)

        assert not spy.called


@pytest.fixture
def mock_transaction(db_session):
    transaction = mock.Mock(spec=db_session.transaction)
    type(transaction).parent = mock.PropertyMock(return_value=None)
    return transaction
