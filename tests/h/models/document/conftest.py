from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest


@pytest.fixture()
def mock_db_session(db_session):
    return Mock(spec=db_session)


def yesterday():
    return datetime.now() - timedelta(days=1)
