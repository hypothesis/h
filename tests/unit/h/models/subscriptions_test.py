from h.models.subscriptions import Subscriptions


class TestSubscriptions:
    def test___repr__(self):
        subscription = Subscriptions(
            uri="http://example.com", type=Subscriptions.Type.REPLY, active=True
        )

        assert (
            repr(subscription)
            == "<Subscription uri=http://example.com type=Type.REPLY active=True>"
        )
