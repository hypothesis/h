from h.auth.util import client_authority
from h.security.acl import ACL
from h.traversal.root import RootFactory


class BulkAPIRoot(RootFactory):
    """Root factory for the Bulk API."""

    def __acl__(self):
        return ACL.for_bulk_api(client_authority=client_authority(self.request))
