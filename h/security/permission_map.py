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

import h.security.predicates as p
from h.security.permissions import Permission
from h.security.predicates import resolve_predicates

PERMISSION_MAP = {
    # Admin pages
    Permission.AdminPage.HIGH_RISK: [[p.user_is_admin]],
    Permission.AdminPage.LOW_RISK: [[p.user_is_admin], [p.user_is_staff]],
    # User modification permissions
    Permission.User.CREATE: [[p.authenticated_client]],
    Permission.User.UPDATE: [[p.user_authority_matches_authenticated_client]],
    Permission.User.READ: [[p.user_authority_matches_authenticated_client]],
    # Bulk API - Currently only LMS uses this end-point
    Permission.API.BULK_ACTION: [[p.authenticated_client_is_lms]],
    # A user can always update their own profile
    Permission.Profile.UPDATE: [[p.authenticated_user]],
    # --------------------------------------------------------------------- #
    # Groups
    Permission.Group.CREATE: [[p.authenticated_user]],
    Permission.Group.WRITE: [
        [p.group_writable_by_authority, p.group_matches_user_authority],
        [p.group_writable_by_members, p.group_has_user_as_member],
    ],
    Permission.Group.JOIN: [
        [p.group_joinable_by_authority, p.group_matches_user_authority]
    ],
    Permission.Group.READ: [
        [p.group_readable_by_world],
        [p.group_readable_by_members, p.group_has_user_as_member],
        [p.group_matches_authenticated_client_authority],
    ],
    Permission.Group.FLAG: [
        # Any logged in user should be able to flag things they can see
        [p.group_readable_by_world, p.authenticated],
        [p.group_readable_by_members, p.group_has_user_as_member],
    ],
    Permission.Group.EDIT: [
        [p.group_matches_authenticated_client_authority],
        [p.group_has_user_as_owner],
        [p.group_has_user_as_admin],
        [p.group_has_user_as_moderator],
    ],
    Permission.Group.MEMBER_ADD: [[p.group_matches_authenticated_client_authority]],
    Permission.Group.MODERATE: [[p.group_created_by_user]],
    # --------------------------------------------------------------------- #
    # Annotations
    Permission.Annotation.CREATE: [[p.authenticated]],
    # You can be notified about an annotation even if it's been deleted
    Permission.Annotation.READ_REALTIME_UPDATES: [
        [p.annotation_not_shared, p.annotation_created_by_user],
        # For shared annotations the permissions are copied from the group
        # of the annotation. We bend the predicate system here a little and
        # put a raw permission in which will cause us to look up that
        # permission.
        [p.annotation_shared, Permission.Group.READ],
    ],
    Permission.Annotation.READ: [
        [p.annotation_live, p.annotation_not_shared, p.annotation_created_by_user],
        [p.annotation_live, p.annotation_shared, Permission.Group.READ],
    ],
    Permission.Annotation.FLAG: [
        [p.annotation_live, p.annotation_not_shared, p.annotation_created_by_user],
        [p.annotation_live, p.annotation_shared, Permission.Group.FLAG],
    ],
    Permission.Annotation.MODERATE: [
        [p.annotation_live, p.annotation_shared, Permission.Group.MODERATE]
    ],
    # The user who created the annotation always has the these permissions
    Permission.Annotation.UPDATE: [[p.annotation_live, p.annotation_created_by_user]],
    Permission.Annotation.DELETE: [[p.annotation_live, p.annotation_created_by_user]],
}

# Predicates can define parents which they need to be true before they are
# true. We don't put all the parents here because it would be fiddly and make
# it harder to read.

# This turns the abstract predicates above into lists which include all of
# their parents in the correct order to evaluate them.
PERMISSION_MAP = resolve_predicates(PERMISSION_MAP)
