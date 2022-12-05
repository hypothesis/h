from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.models import Subscriptions
from h.services import SubscriptionService
from h.services.subscription import service_factory


class TestSubscriptionService:
    def test_get_subscription(self, svc, reply_subscription):
        result = svc.get_subscription(
            user_id=reply_subscription.uri, type_=Subscriptions.Type.REPLY
        )

        assert result == reply_subscription
        assert result.active == reply_subscription.active

    def test_get_subscription_with_a_missing_subscription(self, svc):
        result = svc.get_subscription(
            user_id="acct:new_user@example.com", type_=Subscriptions.Type.REPLY
        )

        assert result == Any.instance_of(Subscriptions).with_attrs(
            {
                "uri": "acct:new_user@example.com",
                "type": Subscriptions.Type.REPLY.value,
                "active": True,
            }
        )

    @pytest.fixture
    def reply_subscription(self, factories):
        # Despite being named in the plural, this is only one subscription
        return factories.Subscriptions(type=Subscriptions.Type.REPLY.value)

    @pytest.fixture
    def svc(self, db_session):
        return SubscriptionService(db_session=db_session)

    @pytest.fixture(autouse=True)
    def subscription_noise(self, factories):
        factories.Subscriptions.create_batch(3)


class TestServiceFactory:
    def test_it(self, pyramid_request, SubscriptionService):
        svc = service_factory(sentinel.context, pyramid_request)

        SubscriptionService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == SubscriptionService.return_value

    @pytest.fixture
    def SubscriptionService(self, patch):
        return patch("h.services.subscription.SubscriptionService")
