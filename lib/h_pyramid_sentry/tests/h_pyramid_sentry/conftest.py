# pylint: disable=no-self-use
"""
The `conftest` module is automatically loaded by pytest and serves as a place
to put fixture functions that are useful application-wide.
"""
import functools
import pytest

from unittest import mock


def _autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(_autopatcher, request)
