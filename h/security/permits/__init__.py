from h.security.permits.engine import PredicateBasedPermissions
from h.security.permits.permission_map import PERMISSION_MAP

ENGINE = PredicateBasedPermissions(PERMISSION_MAP)


__all__ = ("permits",)


def permits(identity, context, permission):
    return ENGINE.permits(identity, context, permission)
