"""
A method of working out which permissions are available.

This is based on a map from `Permission`'s to a list of lists of "predicates"
and other permissions. Predicates are simple functions which accept identity
and context objects and return a truthy value.

To tell if a permission is granted we look at the list of lists and see if for
at least one sub-list:

* Every predicate function included evaluates to True
* Every permission included would also be granted (by recursing)
"""

from h.security import Identity, Permission
from h.security.predicates import *

__all__ = ("identity_permits",)


PERMISSION_MAP = {
    # Admin pages
    Permission.AdminPage.ADMINS: [[user_is_admin]],
    Permission.AdminPage.BADGE: [[user_is_admin]],
    Permission.AdminPage.FEATURES: [[user_is_admin]],
    Permission.AdminPage.GROUPS: [[user_is_admin], [user_is_staff]],
    Permission.AdminPage.INDEX: [[user_is_admin], [user_is_staff]],
    Permission.AdminPage.MAILER: [[user_is_admin], [user_is_staff]],
    Permission.AdminPage.OAUTH_CLIENTS: [[user_is_admin]],
    Permission.AdminPage.ORGANIZATIONS: [[user_is_admin], [user_is_staff]],
    Permission.AdminPage.NIPSA: [[user_is_admin]],
    Permission.AdminPage.SEARCH: [[user_is_admin]],
    Permission.AdminPage.STAFF: [[user_is_admin]],
    Permission.AdminPage.USERS: [[user_is_admin], [user_is_staff]],
    # User modification permissions
    Permission.User.CREATE: [[authenticated_client]],
    Permission.User.UPDATE: [[user_authority_matches_authenticated_client]],
    Permission.User.READ: [[user_authority_matches_authenticated_client]],
    # Bulk API - Currently only LMS uses this end-point
    Permission.API.BULK_ACTION: [[authenticated_client_is_lms]],
    # A user can always update their own profile
    Permission.Profile.UPDATE: [[authenticated_user]],
    # --------------------------------------------------------------------- #
    # Groups
    Permission.Group.CREATE: [[authenticated_user]],
    Permission.Group.WRITE: [
        [group_writable_by_authority, group_matches_user_authority],
        [group_writable_by_members, group_has_user_as_member],
    ],
    Permission.Group.JOIN: [
        [group_joinable_by_authority, group_matches_user_authority]
    ],
    Permission.Group.READ: [
        [group_readable_by_world],
        [group_readable_by_members, group_has_user_as_member],
        [group_authority_matches_authenticated_client],
    ],
    Permission.Group.MEMBER_READ: [
        [group_readable_by_world],
        [group_readable_by_members, group_has_user_as_member],
        [group_authority_matches_authenticated_client],
    ],
    Permission.Group.FLAG: [
        # Any logged in user should be able to flag things they can see
        [group_readable_by_world, authenticated],
        [group_readable_by_members, group_has_user_as_member],
    ],
    Permission.Group.EDIT: [
        [group_authority_matches_authenticated_client],
        [group_created_by_user],
    ],
    Permission.Group.MEMBER_ADD: [[group_authority_matches_authenticated_client]],
    Permission.Group.MODERATE: [[group_created_by_user]],
    Permission.Group.UPSERT: [
        [group_created_by_user],
        [group_not_found, authenticated_user],
    ],
    # --------------------------------------------------------------------- #
    # Annotations
    Permission.Annotation.CREATE: [[authenticated]],
    # You can be notified about an annotation even if it's been deleted
    Permission.Annotation.READ_REALTIME_UPDATES: [
        [annotation_not_shared, annotation_created_by_user],
        # For shared annotations the permissions are copied from the group
        # of the annotation. We bend the predicate system here a little and
        # put a raw permission in which will cause us to look up that
        # permission.
        [annotation_shared, Permission.Group.READ],
    ],
    Permission.Annotation.READ: [
        [annotation_live, annotation_not_shared, annotation_created_by_user],
        [annotation_live, annotation_shared, Permission.Group.READ],
    ],
    Permission.Annotation.FLAG: [
        [annotation_live, annotation_not_shared, annotation_created_by_user],
        [annotation_live, annotation_shared, Permission.Group.FLAG],
    ],
    Permission.Annotation.MODERATE: [
        [annotation_live, annotation_shared, Permission.Group.MODERATE]
    ],
    # The user who created the annotation always has the these permissions
    Permission.Annotation.UPDATE: [[annotation_live, annotation_created_by_user]],
    Permission.Annotation.DELETE: [[annotation_live, annotation_created_by_user]],
}

# Predicates can define parents which they need to be true before they are
# true. We don't put all the parents here because it would be fiddly and make
# it harder to read.

# This turns the abstract predicates above into lists which include all of
# their parents in the correct order to evaluate them.
PERMISSION_MAP = resolve_predicates(PERMISSION_MAP)


def identity_permits_clear(identity: Identity, context, permission) -> bool:
    """
    Check whether a given identity has permission to operate on a context.

    For example the identity might include a user, and the context a group
    and the permission might ask whether the user can edit that group.

    :param identity: Identity object of the user
    :param context: Context object representing the objects acted upon
    :param permission: Permission requested
    """

    if clauses := PERMISSION_MAP.get(permission):
        for clause in clauses:
            all_ok = True
            for predicate in clause:
                if _predicate_true(predicate, identity, context):
                    print(predicate, "? Yes")
                    continue
                else:
                    print(predicate, "? NO")
                    all_ok = False
                    break

            if all_ok:
                print(f"Clause {clause} grants {permission}")
                return True

    return False


def identity_permits(identity: Identity, context, permission) -> bool:
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
        return any(
            # .. *all* elements in it are true
            all(_predicate_true(predicate, identity, context) for predicate in clause)
            for clause in clauses
        )

    return False


def _predicate_true(predicate, identity, context):
    """Check whether a predicate is true."""
    try:
        return predicate(identity, context)

    # If the "predicate" isn't callable, we'll assume it's a permission
    # and work out if we have that permission
    except TypeError:
        return identity_permits(identity, context, predicate)
