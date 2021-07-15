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
        (Allow, role.Staff, Permission.ADMINPAGE_INDEX),
        (Allow, role.Staff, Permission.ADMINPAGE_GROUPS),
        (Allow, role.Staff, Permission.ADMINPAGE_MAILER),
        (Allow, role.Staff, Permission.ADMINPAGE_ORGANIZATIONS),
        (Allow, role.Staff, Permission.ADMINPAGE_USERS),
        (Allow, role.Admin, ALL_PERMISSIONS),
        DENY_ALL,
    ]
