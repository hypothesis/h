# -*- coding: utf-8 -*-
"""Defines unit tests for h.assets."""
from mock import Mock
from pyramid.urldispatch import Route
from pyramid.testing import DummyRequest, testConfig

from h import assets


class DummyEvent(object):
    """A dummy event for testing registry events."""
    # pylint: disable=too-few-public-methods

    def __init__(self, request):
        self.request = request


def test_subscriber_predicate(settings):
    """Test that the ``asset_request`` subscriber predicate.

    It should correctly match asset requests when its value is ``True``,
    and other requests when ``False``.
    """
    mock1 = Mock()
    mock2 = Mock()

    with testConfig(settings=settings) as config:
        # pylint: disable=attribute-defined-outside-init
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
