from h.security import ACL
from h.traversal.root import RootFactory


class ProfileRoot(RootFactory):
    """Sets a simple Root for API profile endpoints."""

    @classmethod
    def __acl__(cls):
        return ACL.for_profile()
