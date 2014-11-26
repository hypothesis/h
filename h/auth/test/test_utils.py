from mock import MagicMock
from pyramid import testing

from h import interfaces
from h.auth import utils


def test_get_consumer_default():
    mock_consumer = MagicMock()
    settings = {'api.key': '1234'}
    with testing.testConfig(settings=settings) as config:
        registry = config.registry
        registry.registerUtility(mock_consumer, interfaces.IConsumerClass)
        request = testing.DummyRequest(registry=config.registry)
        utils.get_consumer(request)
        mock_consumer.get_by_key.assert_called_once_with(request, '1234')


def test_get_consumer_default_with_secret():
    mock_consumer = MagicMock()
    settings = {'api.key': '1234', 'api.secret': 'secret'}
    with testing.testConfig(settings=settings) as config:
        registry = config.registry
        registry.registerUtility(mock_consumer, interfaces.IConsumerClass)
        request = testing.DummyRequest(registry=config.registry)
        utils.get_consumer(request)
        mock_consumer.assert_called_once_with(key='1234', secret='secret')


def test_get_consumer_specific():
    mock_consumer = MagicMock()
    settings = {'api.key': '1234'}
    with testing.testConfig(settings=settings) as config:
        registry = config.registry
        registry.registerUtility(mock_consumer, interfaces.IConsumerClass)
        request = testing.DummyRequest(registry=config.registry)
        utils.get_consumer(request, '4321')
        mock_consumer.get_by_key.assert_called_with(request, '4321')


def test_get_consumer_fail():
    mock_consumer = MagicMock()
    mock_consumer.get_by_key.return_value = None
    settings = {'api.key': '1234'}
    with testing.testConfig(settings=settings) as config:
        registry = config.registry
        registry.registerUtility(mock_consumer, interfaces.IConsumerClass)
        request = testing.DummyRequest(registry=config.registry)
        assert utils.get_consumer(request, '9876') is None
