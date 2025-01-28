"""Data classes used to represent authenticated users."""

from dataclasses import dataclass, field
from typing import Self

from h.models import AuthClient, Group, GroupMembershipRoles, User


@dataclass
class LongLivedMembership:
    """A membership object that isn't connected to SQLAlchemy."""

    group: "LongLivedGroup"
    user: "LongLivedUser"
    roles: list[str]


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
    staff: bool
    admin: bool
    memberships: list[LongLivedMembership] = field(default_factory=list)

    @classmethod
    def from_model(cls, user: User):
        """Create a long lived model from a DB model object."""

        long_lived_user = LongLivedUser(
            id=user.id,
            userid=user.userid,
            authority=user.authority,
            admin=user.admin,
            staff=user.staff,
        )

        groups = {}

        for membership in user.memberships:
            groups.setdefault(
                membership.group.id, LongLivedGroup.from_model(membership.group)
            )
            long_lived_user.memberships.append(
                LongLivedMembership(
                    group=groups[membership.group.id],
                    user=long_lived_user,
                    roles=membership.roles,
                )
            )

        return long_lived_user


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

    user: LongLivedUser | None = None
    auth_client: LongLivedAuthClient | None = None

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

    def get_roles(self, group) -> list[GroupMembershipRoles]:
        """Return this identity's roles in `group`."""
        if self.user is None:
            return []

        for membership in self.user.memberships:
            if membership.group.id == group.id:
                return membership.roles

        return []
