from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from h.auth import role
from h.auth.util import client_authority
from h.exceptions import InvalidUserId
from h.traversal.root import RootFactory


class UserContext:
    """Context for user-centered views."""

    def __init__(self, user):
        self.user = user

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


class UserByNameRoot(UserRoot):
    """Root factory for routes which look up users by username."""

    def __getitem__(self, username):
        authority = client_authority(self.request) or self.request.default_authority
        user = self.user_service.fetch(username, authority)

        if not user:
            raise KeyError()

        # TODO: This should be a UserContext
        return user


class UserByIDRoot(UserRoot):
    """Root factory for routes which look up users by id."""

    def __getitem__(self, userid):
        try:
            user = self.user_service.fetch(userid)
        except InvalidUserId as e:
            # In this context we failed because the user provided a userid
            # we cannot parse, not because it could not be found
            raise HTTPBadRequest(e.args[0]) from e

        if not user:
            raise KeyError()

        return UserContext(user)
