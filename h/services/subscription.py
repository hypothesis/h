from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session
from webob.cookies import SignedSerializer

from h.models import Subscriptions
from h.security import derive_key


class InvalidUnsubscribeToken(Exception):
    """When an unsubscribe token has an invalid format."""


class SubscriptionService:
    """A service for managing user communication preferences."""

    MISSING_SUBSCRIPTION_ACTIVE = True
    """Default behavior when we find a missing subscription."""

    def __init__(self, db_session: Session, secret: bytes, salt: bytes):
        self._db_session = db_session
        self._token_serializer = SignedSerializer(
            secret=derive_key(key_material=secret, salt=salt, info=b"h.notification"),
            salt=None,
        )

    def get_subscription(
        self, user_id: str, type_: Subscriptions.Type
    ) -> Subscriptions:
        """
        Get a subscription for a user, creating if it is missing.

        :param user_id: Fully qualified user id (like 'acct:...')
        :param type_: Subscription type
        """
        subscription = (
            self._db_session.query(Subscriptions)
            .filter(func.lower(Subscriptions.uri) == func.lower(user_id))
            .filter(Subscriptions.type == type_.value)
            .one_or_none()
        )

        if not subscription:
            subscription = Subscriptions(
                uri=user_id, type=type_, active=self.MISSING_SUBSCRIPTION_ACTIVE
            )
            self._db_session.add(subscription)

        return subscription

    def get_all_subscriptions(self, user_id: str) -> List[Subscriptions]:
        """
        Get all subscriptions for a particular user, creating any missing ones.

        :param user_id: User id to get the subscriptions of
        """
        return [self.get_subscription(user_id, type_) for type_ in Subscriptions.Type]

    def get_unsubscribe_token(self, user_id: str, type_: Subscriptions.Type) -> str:
        """
        Create a signed token encoding a user and subscription type.

        This is intended to be placed in an email, so we can verify that a user
        wants to unsubscribe from a particular subscription.

        :param user_id: User id to unsubscribe
        :param type_: The subscription type to unsubscribe from
        """
        return self._token_serializer.dumps({"type": type_.value, "uri": user_id})

    def unsubscribe_using_token(self, token: str):
        """
        Unsubscribes a user based on details encoded in an unsubscribe token.

        :param token: A token provided by `get_unsubscribe_token()`
        :raises InvalidUnsubscribeToken: When the token format is invalid
        """
        try:
            payload = self._token_serializer.loads(token)
        except ValueError as err:
            raise InvalidUnsubscribeToken() from err

        self.get_subscription(
            user_id=payload["uri"], type_=Subscriptions.Type(payload["type"])
        ).active = False


def service_factory(_context, request) -> SubscriptionService:
    """Generate a subscription service object."""

    return SubscriptionService(
        db_session=request.db,
        secret=request.registry.settings["secret_key"],
        salt=request.registry.settings["secret_salt"],
    )
