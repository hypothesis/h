from unittest import mock
from unittest.mock import sentinel

import pytest

from h.streamer.db import get_session, read_only_transaction
from h.streamer.streamer import UnknownMessageType


class TestMakeSession:
    def test_it(self, db):
        session = get_session(sentinel.settings)

        db.make_engine.assert_called_once_with(sentinel.settings)
        db.Session.assert_called_once_with(bind=db.make_engine.return_value)
        assert session == db.Session.return_value

    @pytest.fixture
    def db(self, patch):
        return patch("h.streamer.db.db")


class TestReadOnlyTransaction:
    def test_it_starts_a_read_only_transaction(self, session):
        with read_only_transaction(session):
            ...

        assert session.method_calls[0] == mock.call.execute(
            "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE READ ONLY DEFERRABLE"
        )

    def test_it_calls_closes_correctly(self, session):
        with read_only_transaction(session):
            ...

        assert session.method_calls[-2:] == [mock.call.commit(), mock.call.close()]

    @pytest.mark.parametrize("exception", (UnknownMessageType, RuntimeError))
    def test_it_rolls_back_on_handler_exception(self, session, exception):
        with read_only_transaction(session):
            raise exception()

        self._assert_rollback_and_close(session)

    @pytest.mark.parametrize("exception", (KeyboardInterrupt, SystemExit))
    def test_it_reraises_certain_exceptions(self, session, exception):
        with pytest.raises(exception):
            with read_only_transaction(session):
                raise exception

        self._assert_rollback_and_close(session)

    def _assert_rollback_and_close(self, session):
        session.commit.assert_not_called()
        assert session.method_calls[-2:] == [mock.call.rollback(), mock.call.close()]

    @pytest.fixture
    def session(self):
        return mock.Mock(spec_set=["close", "commit", "execute", "rollback"])
