from pyramid.security import Allow

from h.traversal.root import RootFactory


class BulkAPIRoot(RootFactory):
    """Root factory for the Bulk API."""

    # Currently only LMS uses this end-point
    __acl__ = [(Allow, "client_authority:lms.hypothes.is", "bulk_action")]
