from h.security.acl import ACL


class RootFactory:
    """Base class for all root resource factories."""

    def __init__(self, request):
        self.request = request


class Root(RootFactory):
    """This app's default root factory."""

    @classmethod
    def __acl__(cls):
        return ACL.for_admin_pages()
