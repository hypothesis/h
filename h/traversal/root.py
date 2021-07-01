from pyramid.security import ALL_PERMISSIONS, DENY_ALL, Allow

from h.auth import role


class RootFactory:
    """Base class for all root resource factories."""

    def __init__(self, request):
        self.request = request


class Root(RootFactory):
    """This app's default root factory."""

    __acl__ = [
        (Allow, role.Staff, "admin_index"),
        (Allow, role.Staff, "admin_groups"),
        (Allow, role.Staff, "admin_mailer"),
        (Allow, role.Staff, "admin_organizations"),
        (Allow, role.Staff, "admin_users"),
        (Allow, role.Admin, ALL_PERMISSIONS),
        DENY_ALL,
    ]
