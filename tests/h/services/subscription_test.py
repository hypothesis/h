from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.models import Subscriptions
from h.services import SubscriptionService
from h.services.subscription import InvalidUnsubscribeToken, service_factory


class TestSubscriptionService:
    def test_init(self, derive_key, SignedSerializer):
        SubscriptionService(
            db_session=sentinel.db_session, secret=sentinel.secret, salt=sentinel.salt
        )

        derive_key.assert_called_once_with(
            key_material=sentinel.secret, salt=sentinel.salt, info=b"h.notification"
        )
        SignedSerializer.assert_called_once_with(
            secret=derive_key.return_value, salt=None
        )

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

    def test_get_unsubscribe_token(self, svc, SignedSerializer):
        result = svc.get_unsubscribe_token(
            user_id="acct:user@example.com", type_=Subscriptions.Type.REPLY
        )

        SignedSerializer.return_value.dumps.assert_called_once_with(
            {"type": Subscriptions.Type.REPLY.value, "uri": "acct:user@example.com"}
        )
        assert result == SignedSerializer.return_value.dumps.return_value

    def test_unsubscribe_using_token(self, svc, SignedSerializer, reply_subscription):
        reply_subscription.active = True
        SignedSerializer.return_value.loads.return_value = {
            "uri": reply_subscription.uri,
            "type": reply_subscription.type,
        }

        svc.unsubscribe_using_token(token=sentinel.good_token)

        SignedSerializer.return_value.loads.assert_called_once_with(sentinel.good_token)
        reply_subscription.active = False

    def test_unsubscribe_using_token_with_invalid_token(self, svc, SignedSerializer):
        SignedSerializer.return_value.loads.side_effect = ValueError

        with pytest.raises(InvalidUnsubscribeToken):
            svc.unsubscribe_using_token(token=sentinel.bad_token)

    @pytest.fixture
    def reply_subscription(self, factories):
        # Despite being named in the plural, this is only one subscription
        return factories.Subscriptions(type=Subscriptions.Type.REPLY.value)

    @pytest.fixture
    def svc(self, db_session):
        return SubscriptionService(
            db_session=db_session, secret=b"secret", salt=b"salt"
        )

    @pytest.fixture(autouse=True)
    def derive_key(self, patch):
        return patch("h.services.subscription.derive_key")

    @pytest.fixture(autouse=True)
    def SignedSerializer(self, patch):
        return patch("h.services.subscription.SignedSerializer")

    @pytest.fixture(autouse=True)
    def subscription_noise(self, factories):
        factories.Subscriptions.create_batch(3)


class TestServiceFactory:
    def test_it(self, pyramid_request, SubscriptionService):
        pyramid_request.registry.settings = {
            "secret_key": sentinel.secret_key,
            "secret_salt": sentinel.secret_salt,
        }

        svc = service_factory(sentinel.context, pyramid_request)

        SubscriptionService.assert_called_once_with(
            db_session=pyramid_request.db,
            secret=sentinel.secret_key,
            salt=sentinel.secret_salt,
        )
        assert svc == SubscriptionService.return_value

    @pytest.fixture
    def SubscriptionService(self, patch):
        return patch("h.services.subscription.SubscriptionService")
