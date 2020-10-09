from unittest import mock

import pytest


@pytest.fixture
def group_service():
    return mock.Mock(spec_set=["find"])
