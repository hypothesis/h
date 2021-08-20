from typing import Optional

from pyramid.authorization import Authenticated, Everyone

from h.security.identity import Identity
from h.security.role import Role


def principals_for_identity(identity: Optional[Identity]):
    """
    Get the security principals for a given identity.

    Any identity which is passed is assumed to have passed authentication.
    Passing None instead will return principals for an unauthenticated user.

    :param identity: Identity to provide principals for or None
    :returns: A list of principals
    """

    principals = {Everyone}

    if not identity:
        return list(principals)

    principals.add(Authenticated)

    if user := identity.user:
        principals.add(identity.user.userid)

        principals.add(Role.USER)
        if user.admin:
            principals.add(Role.ADMIN)
        if user.staff:
            principals.add(Role.STAFF)

        for group in user.groups:
            principals.add("group:{group.pubid}".format(group=group))

        principals.add("authority:{authority}".format(authority=user.authority))

    if auth_client := identity.auth_client:
        principals.add(identity.auth_client.id)
        principals.add(Role.AUTH_CLIENT)

        principals.add(f"client:{auth_client.id}@{auth_client.authority}")
        principals.add(f"client_authority:{auth_client.authority}")

    if identity.auth_client and identity.user:
        principals.add(Role.AUTH_CLIENT_FORWARDED_USER)

    return list(principals)
