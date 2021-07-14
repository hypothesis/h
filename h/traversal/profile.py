from pyramid.security import Allow

from h.auth import role
from h.security.permissions import Permission
from h.traversal.root import RootFactory


class ProfileRoot(RootFactory):
    """
    Simple Root for API profile endpoints
    """

    __acl__ = [(Allow, role.User, Permission.Profile.UPDATE)]
