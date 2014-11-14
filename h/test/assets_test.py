# -*- coding: utf-8 -*-
"""Defines unit tests for h.assets."""
from mock import Mock
from pyramid.paster import get_appsettings
from pyramid.urldispatch import Route
from pyramid.testing import DummyRequest, testConfig
import pytest

from h import assets


class DummyEvent(object):
    """A dummy event for testing registry events."""

    def __init__(self, request):
        self.request = request


@pytest.fixture
def settings():
    settings = get_appsettings('development.ini')
    settings['bind'] = 'localhost:4000'
    settings['es.index'] = 'annotator-test'
    settings['sqlalchemy.url'] = 'sqlite:///test.db'
    settings.update({
        'basemodel.should_create_all': 'True',
        'basemodel.should_drop_all': 'True',
    })
    return settings


def test_subscriber_predicate(settings):
    """Test that the ``asset_request`` subscriber predicate.

    It should correctly match asset requests when its value is ``True``,
    and other requests when ``False``.
    """
    mock1 = Mock()
    mock2 = Mock()

    with testConfig(settings=settings) as config:
        config.include(assets)
        config.add_subscriber(mock1, DummyEvent, asset_request=False)
        config.add_subscriber(mock2, DummyEvent, asset_request=True)

        request1 = DummyRequest('/')
        request1.matched_route = None

        pattern = config.get_webassets_env().url + '*subpath'
        request2 = DummyRequest(config.get_webassets_env().url + '/t.png')
        request2.matched_route = Route('__' + pattern, pattern)

        event1 = DummyEvent(request1)
        event2 = DummyEvent(request2)

        config.registry.notify(event1)
        config.registry.notify(event2)

        mock1.assert_called_onceventwith(event1)
        mock2.assert_called_onceventwith(event2)
