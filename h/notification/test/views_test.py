# -*- coding: utf-8 -*-

import mock
from pyramid.testing import DummyRequest
import pytest

from h import db
from h.models import Subscriptions
from h.notification import views


@pytest.mark.usefixtures('subscriptions', 'token_serializer')
class TestUnsubscribe(object):

    def test_deserializes_token(self, token_serializer):
        request = DummyRequest(matchdict={'token': 'wibble'}, db=db.Session)

        views.unsubscribe(request)

        token_serializer.loads.assert_called_once_with('wibble')

    def test_successfully_unsubscribes_user(self, subscriptions, token_serializer):
        sub1, _, _ = subscriptions
        request = DummyRequest(matchdict={'token': 'wibble'}, db=db.Session)
        token_serializer.loads.return_value = {'type': 'reply', 'uri': 'acct:foo@example.com'}

        views.unsubscribe(request)

        assert not sub1.active

    def test_ignores_other_subscriptions(self, subscriptions, token_serializer):
        _, sub2, sub3 = subscriptions
        request = DummyRequest(matchdict={'token': 'wibble'}, db=db.Session)
        token_serializer.loads.return_value = {'type': 'reply', 'uri': 'acct:foo@example.com'}

        views.unsubscribe(request)

        assert sub2.active
        assert sub3.active

    def test_multiple_calls_ok(self, subscriptions, token_serializer):
        sub1, _, _ = subscriptions
        request = DummyRequest(matchdict={'token': 'wibble'}, db=db.Session)
        token_serializer.loads.return_value = {'type': 'reply', 'uri': 'acct:foo@example.com'}

        views.unsubscribe(request)
        views.unsubscribe(request)

        assert not sub1.active

    def test_raises_not_found_if_token_invalue(self, token_serializer):
        from pyramid.exceptions import HTTPNotFound
        request = DummyRequest(matchdict={'token': 'wibble'}, db=db.Session)
        token_serializer.loads.side_effect = ValueError('token invalid')

        with pytest.raises(HTTPNotFound):
            views.unsubscribe(request)

    @pytest.fixture
    def subscriptions(self):
        subs = [
            Subscriptions(type='reply', uri='acct:foo@example.com', active=True),
            Subscriptions(type='dingo', uri='acct:foo@example.com', active=True),
            Subscriptions(type='reply', uri='acct:bar@example.com', active=True),
        ]
        db.Session.add_all(subs)
        db.Session.flush()
        return subs

    @pytest.fixture
    def token_serializer(self, config):
        serializer = mock.Mock(spec_set=['loads'])
        serializer.loads.return_value = {'type': 'matches', 'uri': 'nothing'}
        config.registry.notification_serializer = serializer
        return serializer
