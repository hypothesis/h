from dataclasses import dataclass

from pyramid.httpexceptions import HTTPBadRequest

from h.exceptions import InvalidUserId
from h.models import User


@dataclass
class UserContext:
    """Context for user-centered views."""

    user: User


class UserRoot:
    def __init__(self, request):
        self.request = request
        self.user_service = self.request.find_service(name="user")

    def get_user_context(self, userid_or_username, authority):
        """Get a user while handling errors appropriately for a traversal."""

        try:
            user = self.user_service.fetch(userid_or_username, authority)

        except InvalidUserId as err:
            raise HTTPBadRequest(err.args[0]) from err

        if not user:
            raise KeyError()

        return UserContext(user)


class UserByNameRoot(UserRoot):
    """Root factory for routes which look up users by username."""

    def __getitem__(self, username):
        return self.get_user_context(
            username, authority=self.request.effective_authority
        )


class UserByIDRoot(UserRoot):
    """Root factory for routes which look up users by id."""

    def __getitem__(self, userid):
        return self.get_user_context(userid, authority=None)
