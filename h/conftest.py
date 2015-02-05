# -*- coding: utf-8 -*-
"""
The `conftest` module is automatically loaded by py.test and serves as a place
to put fixture functions that are useful application-wide.
"""
import pytest

from pyramid import testing
from pyramid.paster import get_appsettings


@pytest.fixture(scope='session', autouse=True)
def settings():
    """Default app settings (test.ini)."""
    return get_appsettings('test.ini')


@pytest.fixture(autouse=True)
def config(request, settings):
    """Pyramid configurator object."""
    req = testing.DummyRequest()
    config = testing.setUp(request=req, settings=settings)

    def destroy():
        testing.tearDown()

    request.addfinalizer(destroy)

    return config
