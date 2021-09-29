import warnings
from logging import getLogger
from typing import Optional

from pyramid.authorization import ACLAuthorizationPolicy

from h.security import permission_map
from h.security.identity import Identity
from h.security.principals import principals_for_identity

LOG = getLogger(__name__)


def identity_permits(identity: Optional[Identity], context, permission) -> bool:
    """
    Get whether a given identity has the requested permission on the context.

    :param identity: Identity object or None for non authenticated access
    :param context: A context object
    :param permission: The permission requested
    """

    acl_allows = bool(
        ACLAuthorizationPolicy().permits(
            context=context,
            principals=principals_for_identity(identity),
            permission=permission,
        )
    )

    try:
        map_allows = permission_map.identity_permits(identity, context, permission)
    # pylint: disable=broad-except
    except Exception as err:  # pragma: no cover
        map_allows = err  # pylint: disable=redefined-variable-type

    if map_allows != acl_allows:  # pragma: no cover
        message = f"Permissions system disagree about {permission}: ACL={acl_allows}, MAP={map_allows}"
        warnings.warn(message, PendingDeprecationWarning)
        LOG.warning(message)

    return acl_allows
