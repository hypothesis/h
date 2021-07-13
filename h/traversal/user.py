from dataclasses import dataclass

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from h.auth import role
from h.auth.util import client_authority
from h.exceptions import InvalidUserId
from h.models import User
from h.traversal.root import RootFactory


@dataclass
class UserContext:
    """Context for user-centered views."""

    user: User

    def __acl__(self):
        """
        Set the "read" permission for AuthClients that have a matching authority
        to the user. This supercedes the ACL in `h.models.User`.
        """

        return [(Allow, f"client_authority:{self.user.authority}", "read")]


class UserRoot(RootFactory):
    __acl__ = [(Allow, role.AuthClient, "create")]

    def __init__(self, request):
        super().__init__(request)

        self.user_service = self.request.find_service(name="user")

    def get_user(self, userid_or_username, authority):
        """Get a user while handling errors appropriately for a traversal."""

        try:
            user = self.user_service.fetch(userid_or_username, authority)

        except InvalidUserId as err:
            raise HTTPBadRequest(err.args[0]) from err

        if not user:
            raise KeyError()

        return user


class UserByNameRoot(UserRoot):
    """Root factory for routes which look up users by username."""

    def __getitem__(self, username):
        # TODO: This should be a UserContext
        return self.get_user(
            username,
            authority=client_authority(self.request) or self.request.default_authority,
        )


class UserByIDRoot(UserRoot):
    """Root factory for routes which look up users by id."""

    def __getitem__(self, userid):
        return UserContext(self.get_user(userid, authority=None))
