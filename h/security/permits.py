from typing import Optional

from pyramid.authorization import ACLAuthorizationPolicy

from h.security import permission_map
from h.security.identity import Identity
from h.security.principals import principals_for_identity


def identity_permits(identity: Optional[Identity], context, permission) -> bool:
    """
    Get whether a given identity has the requested permission on the context.

    :param identity: Identity object or None for non authenticated access
    :param context: A context object
    :param permission: The permission requested
    """

    map_allows = permission_map.identity_permits(identity, context, permission)
    acl_allows = ACLAuthorizationPolicy().permits(
        context=context,
        principals=principals_for_identity(identity),
        permission=permission,
    )

    assert map_allows == acl_allows, "Permissions systems agree"

    return map_allows
