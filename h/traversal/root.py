from pyramid.security import ALL_PERMISSIONS, DENY_ALL, Allow

from h.auth import role
from h.security.permissions import Permission


class RootFactory:
    """Base class for all root resource factories."""

    def __init__(self, request):
        self.request = request


class Root(RootFactory):
    """This app's default root factory."""

    __acl__ = [
        (Allow, role.Staff, Permission.AdminPage.INDEX),
        (Allow, role.Staff, Permission.AdminPage.GROUPS),
        (Allow, role.Staff, Permission.AdminPage.MAILER),
        (Allow, role.Staff, Permission.AdminPage.ORGANIZATIONS),
        (Allow, role.Staff, Permission.AdminPage.USERS),
        (Allow, role.Admin, ALL_PERMISSIONS),
        DENY_ALL,
    ]
