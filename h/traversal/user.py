from pyramid.httpexceptions import HTTPBadRequest
from pyramid.security import Allow

from h.auth import role
from h.auth.util import client_authority
from h.exceptions import InvalidUserId
from h.security.permissions import Permission
from h.traversal.root import RootFactory


class UserContext:
    """
    Context for user-centered views

    .. todo:: Most views still traverse using ``username`` and work directly
       with User models (:class:`h.models.User`). This context should be
       expanded as we continue to move over to a more resource-based approach.
    """

    def __init__(self, user):
        self.user = user

    def __acl__(self):
        """
        Set the "read" permission for AuthClients that have a matching authority
        to the user. This supercedes the ACL in :class:`h.models.User`.

        .. todo:: This ACL should be expanded (as needed) as more views make use of
        a context versus a model directly.
        """
        acl = []

        user_authority_principal = f"client_authority:{self.user.authority}"
        acl.append((Allow, user_authority_principal, Permission.User.READ))

        return acl


class UserRoot(RootFactory):
    """
    Root factory for routes which traverse Users by ``username``

    FIXME: This class should return UserContext objects, not User objects.

    """

    __acl__ = [(Allow, role.AuthClient, Permission.User.CREATE)]

    def __init__(self, request):
        super().__init__(request)
        self.user_svc = self.request.find_service(name="user")

    def __getitem__(self, username):
        authority = client_authority(self.request) or self.request.default_authority
        user = self.user_svc.fetch(username, authority)

        if not user:
            raise KeyError()

        return user


class UserUserIDRoot(RootFactory):
    """
    Root factory for routes whose context is a :class:`h.traversal.UserContext`.

    .. todo:: This should be the main Root for User objects
    """

    __acl__ = [(Allow, role.AuthClient, Permission.User.CREATE)]

    def __init__(self, request):
        super().__init__(request)
        self.user_svc = self.request.find_service(name="user")

    def __getitem__(self, userid):
        try:
            user = self.user_svc.fetch(userid)
        except InvalidUserId as e:
            # In this context we failed because the user provided a userid
            # we cannot parse, not because it could not be found
            raise HTTPBadRequest(e.args[0]) from e

        if not user:
            raise KeyError()

        return UserContext(user)
