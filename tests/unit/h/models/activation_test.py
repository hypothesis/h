import re

import pytest

from h.models.activation import Activation


class TestActivation:
    def test_code(self, activation):
        assert re.match(r"[A-Za-z0-9]{12}", activation.code)

    def test_get_by_code(self, activation, db_session):
        result = Activation.get_by_code(db_session, code=activation.code)

        assert result == activation

    @pytest.fixture
    def activation(self, db_session):
        activation = Activation()

        db_session.add(activation)
        db_session.flush()

        return activation
