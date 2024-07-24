from typing import Optional

from pyramid.security import Allowed, Denied

from h.security.identity import Identity
from h.security.permission_map import PERMISSION_MAP


def identity_permits(
    identity: Optional[Identity], context, permission
) -> Allowed | Denied:
    """
    Check whether a given identity has permission to operate on a context.

    For example the identity might include a user, and the context a group
    and the permission might ask whether the user can edit that group.

    :param identity: Identity object of the user
    :param context: Context object representing the objects acted upon
    :param permission: Permission requested
    """
    if clauses := PERMISSION_MAP.get(permission):
        # Grant the permissions if for *any* single clause...
        if any(
            # .. *all* elements in it are true
            all(_predicate_true(predicate, identity, context) for predicate in clause)
            for clause in clauses
        ):
            return Allowed("Allowed")

    return Denied("Denied")


def _predicate_true(predicate, identity, context):
    """Check whether a predicate is true."""
    try:
        return predicate(identity, context)

    # If the "predicate" isn't callable, we'll assume it's a permission
    # and work out if we have that permission
    except TypeError:
        return identity_permits(identity, context, predicate)
