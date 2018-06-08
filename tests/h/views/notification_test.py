# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.models import Subscriptions
from h.views.notification import unsubscribe


@pytest.mark.usefixtures("subscriptions", "token_serializer")
class TestUnsubscribe(object):
    def test_deserializes_token(self, pyramid_request, token_serializer):
        pyramid_request.matchdict = {"token": "wibble"}

        unsubscribe(pyramid_request)

        token_serializer.loads.assert_called_once_with("wibble")

    def test_successfully_unsubscribes_user(
        self, pyramid_request, subscriptions, token_serializer
    ):
        sub1, _, _ = subscriptions
        pyramid_request.matchdict = {"token": "wibble"}
        token_serializer.loads.return_value = {
            "type": "reply",
            "uri": "acct:foo@example.com",
        }

        unsubscribe(pyramid_request)

        assert not sub1.active

    def test_ignores_other_subscriptions(
        self, pyramid_request, subscriptions, token_serializer
    ):
        _, sub2, sub3 = subscriptions
        pyramid_request.matchdict = {"token": "wibble"}
        token_serializer.loads.return_value = {
            "type": "reply",
            "uri": "acct:foo@example.com",
        }

        unsubscribe(pyramid_request)

        assert sub2.active
        assert sub3.active

    def test_multiple_calls_ok(self, pyramid_request, subscriptions, token_serializer):
        sub1, _, _ = subscriptions
        pyramid_request.matchdict = {"token": "wibble"}
        token_serializer.loads.return_value = {
            "type": "reply",
            "uri": "acct:foo@example.com",
        }

        unsubscribe(pyramid_request)
        unsubscribe(pyramid_request)

        assert not sub1.active

    def test_raises_not_found_if_token_invalue(self, pyramid_request, token_serializer):
        from pyramid.exceptions import HTTPNotFound

        pyramid_request.matchdict = {"token": "wibble"}
        token_serializer.loads.side_effect = ValueError("token invalid")

        with pytest.raises(HTTPNotFound):
            unsubscribe(pyramid_request)

    @pytest.fixture
    def subscriptions(self, db_session):
        subs = [
            Subscriptions(type="reply", uri="acct:foo@example.com", active=True),
            Subscriptions(type="dingo", uri="acct:foo@example.com", active=True),
            Subscriptions(type="reply", uri="acct:bar@example.com", active=True),
        ]
        db_session.add_all(subs)
        db_session.flush()
        return subs

    @pytest.fixture
    def token_serializer(self, pyramid_config):
        serializer = mock.Mock(spec_set=["loads"])
        serializer.loads.return_value = {"type": "matches", "uri": "nothing"}
        pyramid_config.registry.notification_serializer = serializer
        return serializer
