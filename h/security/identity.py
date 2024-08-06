"""Data classes used to represent authenticated users."""

from dataclasses import dataclass
from typing import List, Optional, Self

from h.models import AuthClient, Group, User


@dataclass
class LongLivedGroup:
    """
    A Group object which isn't connected to SQLAlchemy.

    This is used in a `LongLivedUser` for `Identity.from_models()`
    """

    id: int
    pubid: str

    @classmethod
    def from_model(cls, group: Group):
        """Create a long lived model from a DB model object."""

        return LongLivedGroup(id=group.id, pubid=group.pubid)


@dataclass
class LongLivedUser:
    """
    A User object which isn't connected to SQLAlchemy.

    This is used in `Identity.from_models()`
    """

    id: int
    userid: str
    authority: str
    groups: List[LongLivedGroup]
    staff: bool
    admin: bool

    @classmethod
    def from_model(cls, user: User):
        """Create a long lived model from a DB model object."""

        return LongLivedUser(
            id=user.id,
            userid=user.userid,
            authority=user.authority,
            admin=user.admin,
            staff=user.staff,
            groups=[LongLivedGroup.from_model(group) for group in user.groups],
        )


@dataclass
class LongLivedAuthClient:
    """
    An AuthClient object which isn't connected to SQLAlchemy.

    This is used in `Identity.from_models()`
    """

    id: str
    authority: str

    @classmethod
    def from_model(cls, auth_client: AuthClient):
        """Create a long lived model from a DB model object."""

        return LongLivedAuthClient(id=auth_client.id, authority=auth_client.authority)


@dataclass
class Identity:
    """
    The identity of the logged in user/client.

    This can include a user if the user is directly logged in, or provided via
    a forwarded user. An `AuthClient` if this is a call is made using a
    pre-shared key, or both.
    """

    user: Optional[LongLivedUser] = None
    auth_client: Optional[LongLivedAuthClient] = None

    @classmethod
    def from_models(cls, user: User = None, auth_client: AuthClient = None):
        """Create an `Identity` object from SQLAlchemy models."""

        return Identity(
            user=LongLivedUser.from_model(user) if user else None,
            auth_client=(
                LongLivedAuthClient.from_model(auth_client) if auth_client else None
            ),
        )

    @staticmethod
    def authenticated_userid(identity: Self | None) -> str | None:
        """Return the authenticated_userid from the given identity."""
        if identity and identity.user:
            return identity.user.userid

        return None
