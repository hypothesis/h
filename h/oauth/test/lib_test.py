# -*- coding: utf-8 -*-
from mock import MagicMock
from pyramid import testing

from h.oauth import interfaces, lib


def test_get_client_ok(config):
    mock_factory = MagicMock()
    registry = config.registry
    registry.registerUtility(mock_factory, interfaces.IClientFactory)
    request = testing.DummyRequest(registry=config.registry)
    lib.get_client(request, '4321')
    mock_factory.assert_called_with('4321')


def test_get_client_not_ok(config):
    config.registry.settings.update({'h.client_id': '1234'})
    mock_factory = MagicMock()
    mock_factory.return_value = None
    registry = config.registry
    registry.registerUtility(mock_factory, interfaces.IClientFactory)
    request = testing.DummyRequest(registry=config.registry)
    assert lib.get_client(request, '9876') is None
