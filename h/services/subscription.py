from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from h.models import Subscriptions


class SubscriptionService:
    """A service for managing user communication preferences."""

    MISSING_SUBSCRIPTION_ACTIVE = True
    """Default behavior when we find a missing subscription."""

    def __init__(self, db_session: Session):
        self._db_session = db_session

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


def service_factory(_context, request) -> SubscriptionService:
    """Generate a subscription service object."""

    return SubscriptionService(db_session=request.db)
