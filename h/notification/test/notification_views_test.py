from mock import patch, Mock
from pytest import raises
from pyramid.testing import DummyRequest, testConfig
from webob.cookies import SignedSerializer
from hem.interfaces import IDBSession


def configure(config):
    serializer = SignedSerializer('foobar', 'h.notification.secret')
    config.registry.notification_serializer = serializer
    config.registry.registerUtility(True, IDBSession)


def _unsubscribe_request():
    request = DummyRequest()
    token = request.registry.notification_serializer.dumps({
        'type': 'reply',
        'uri': 'acct:user@localhost',
    })
    request.matchdict['token'] = token
    return request


def test_successful_unsubscribe():
    """ ensure unsubscribe unsets the active flag on the subscription """
    with testConfig() as config:
        configure(config)
        with patch('h.notification.models.Subscriptions'
                   '.get_templates_for_uri_and_type') as mock_subs:
            with patch('hem.db.get_session') as mock_session:
                mock_db = Mock(add=Mock())
                mock_subscription = Mock(active=True)

                mock_subs.return_value = [mock_subscription]
                mock_session.return_value = mock_db

                request = _unsubscribe_request()

                from h.notification.views import unsubscribe
                unsubscribe(request)

                assert mock_subscription.active is False
                mock_db.add.assert_called_with(mock_subscription)


def test_idempotent_unsubscribe():
    """ if called a second time it should not update the model """
    with testConfig() as config:
        configure(config)
        with patch('h.notification.models.Subscriptions'
                   '.get_templates_for_uri_and_type') as mock_subs:
            with patch('hem.db.get_session') as mock_session:
                mock_db = Mock(add=Mock())
                mock_subscription = Mock(active=False)

                mock_subs.return_value = [mock_subscription]
                mock_session.return_value = mock_db

                request = _unsubscribe_request()

                from h.notification.views import unsubscribe
                unsubscribe(request)

                assert mock_subscription.active is False
                assert not mock_db.add.called


def test_invalid_token():
    """It raises an error if an invalid token is provided """
    with testConfig() as config:
        configure(config)
        request = DummyRequest()
        request.matchdict['token'] = 'foobar'

        from h.notification.views import unsubscribe
        with raises(ValueError) as excinfo:
            unsubscribe(request)

        assert str(excinfo.value) == 'Invalid signature'
