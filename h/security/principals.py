from h.security.identity import Identity
from h.security.role import Role


def principals_for_userid(userid, request):
    """
    Return the list of additional principals for a valid userid, or None.

    :param userid: Userid to get principals for
    :param request: Pyramid request object
    :returns: A list of principals or None
    """

    identity = Identity(user=request.find_service(name="user").fetch(userid))

    return principals_for_identity(identity)


def principals_for_identity(identity: Identity):
    """
    Get the security principals for a given identity.

    :param identity: Identity to provide principals for
    :returns: A list of principals or None
    """
    if not identity:
        return None

    principals = set()

    if user := identity.user:
        principals.add(Role.USER)
        if user.admin:
            principals.add(Role.ADMIN)
        if user.staff:
            principals.add(Role.STAFF)
        for group in user.groups:
            principals.add("group:{group.pubid}".format(group=group))
        principals.add("authority:{authority}".format(authority=user.authority))

    if auth_client := identity.auth_client:
        principals.add(f"client:{auth_client.id}@{auth_client.authority}")
        principals.add(f"client_authority:{auth_client.authority}")
        principals.add(Role.AUTH_CLIENT)

    if identity.auth_client and identity.user:
        # Standard pyramid policies like`CallbackAuthenticationPolicy`
        # automatically add the user id in `effective_principals`, but our
        # `h.auth.policy.AuthClientPolicy` overrides it and it's missing
        principals.add(identity.user.userid)
        principals.add(Role.AUTH_CLIENT_FORWARDED_USER)

    if not principals:
        return None

    return list(principals)
