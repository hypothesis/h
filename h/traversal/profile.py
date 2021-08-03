from h.security.acl import ACL
from h.traversal.root import RootFactory


class ProfileRoot(RootFactory):
    """Simple Root for API profile endpoints."""

    @classmethod
    def __acl__(cls):
        return ACL.for_profile()
