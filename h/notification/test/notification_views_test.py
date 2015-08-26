# -*- coding: utf-8 -*-
from mock import patch, Mock
from pytest import raises
from pyramid.testing import DummyRequest as _DummyRequest
from webob.cookies import SignedSerializer

from h.conftest import DummyFeature


class DummyRequest(_DummyRequest):
    def __init__(self, *args, **kwargs):
        params = {
            # Add a dummy feature flag querier to the request
            'feature': DummyFeature(),
        }
        params.update(kwargs)
        super(DummyRequest, self).__init__(*args, **params)


def configure(config):
    serializer = SignedSerializer('foobar', 'h.notification.secret')
    config.registry.notification_serializer = serializer


def _unsubscribe_request():
    request = DummyRequest()
    token = request.registry.notification_serializer.dumps({
        'type': 'reply',
        'uri': 'acct:user@localhost',
    })
    request.matchdict['token'] = token
    return request


def test_successful_unsubscribe(config):
    """ ensure unsubscribe unsets the active flag on the subscription """
    configure(config)
    with patch('h.notification.models.Subscriptions'
               '.get_templates_for_uri_and_type') as mock_subs:
        mock_db = Mock(add=Mock())
        mock_subscription = Mock(active=True)

        mock_subs.return_value = [mock_subscription]

        request = _unsubscribe_request()
        request.db = mock_db

        from h.notification.views import unsubscribe
        unsubscribe(request)

        assert mock_subscription.active is False
        mock_db.add.assert_called_with(mock_subscription)


def test_idempotent_unsubscribe(config):
    """ if called a second time it should not update the model """
    configure(config)
    with patch('h.notification.models.Subscriptions'
               '.get_templates_for_uri_and_type') as mock_subs:
        mock_db = Mock(add=Mock())
        mock_subscription = Mock(active=False)

        mock_subs.return_value = [mock_subscription]

        request = _unsubscribe_request()
        request.db = mock_db

        from h.notification.views import unsubscribe
        unsubscribe(request)

        assert mock_subscription.active is False
        assert not mock_db.add.called


def test_invalid_token(config):
    """It raises an error if an invalid token is provided """
    configure(config)
    request = DummyRequest()
    request.matchdict['token'] = 'foobar'

    from h.notification.views import unsubscribe
    with raises(ValueError) as excinfo:
        unsubscribe(request)

    assert str(excinfo.value) == 'Invalid signature'
