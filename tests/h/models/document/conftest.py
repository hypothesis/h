from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest


@pytest.fixture()
def mock_db_session():
    """Return a mock db session object."""

    class DB:
        def add(self, obj):
            pass

        def query(self, cls):
            pass

        def flush(self):
            pass

    return Mock(spec=DB())


def yesterday():
    return datetime.now() - timedelta(days=1)
