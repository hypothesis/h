# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.util.db import on_transaction_end


class TestOnTransactionEnd(object):
    def test_calls_wrapped_function_when_parent_transaction(self, db_session, mock_transaction):
        spy = mock.Mock()

        @on_transaction_end(db_session)
        def transaction_ended():
            spy()

        db_session.dispatch.after_transaction_end(db_session, mock_transaction)

        spy.assert_called_once_with()

    def test_skips_wrapped_function_when_nested_transaction(self, db_session, mock_transaction):
        spy = mock.Mock()
        type(mock_transaction).parent = mock.PropertyMock(
                return_value=mock.Mock(spec=db_session.transaction))

        @on_transaction_end(db_session)
        def transaction_ended():
            spy()

        db_session.dispatch.after_transaction_end(db_session, mock_transaction)

        assert not spy.called

    @pytest.fixture
    def mock_transaction(self, db_session):
        transaction = mock.Mock(spec=db_session.transaction)
        type(transaction).parent = mock.PropertyMock(return_value=None)
        return transaction
