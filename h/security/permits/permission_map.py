from h.security import Permission
from h.security.permits.predicates import *

PERMISSION_MAP = {
    # Admin pages
    (
        Permission.AdminPage.INDEX,
        Permission.AdminPage.GROUPS,
        Permission.AdminPage.MAILER,
        Permission.AdminPage.ORGANIZATIONS,
        Permission.AdminPage.USERS,
    ): [[user_is_staff]],
    Permission.AdminPage: [[user_is_admin]],
    # User modification permissions
    Permission.User.CREATE: [[authenticated_client]],
    Permission.User.UPDATE: [[user_authority_matches_authenticated_client]],
    Permission.User.READ: [[user_authority_matches_authenticated_client]],
    # Bulk API - Currently only LMS uses this end-point
    Permission.API.BULK_ACTION: [[authenticated_client_is_lms]],
    # A user can always update their own profile
    Permission.Profile.UPDATE: [[authenticated_user]],
    Permission.Group.CREATE: [[authenticated_user]],
    Permission.Group.WRITE: [
        [group_writable_by_authority, group_matches_user_authority],
        [group_writable_by_members, group_has_user_as_member],
    ],
    Permission.Group.JOIN: [
        [group_joinable_by_authority, group_matches_user_authority]
    ],
    (Permission.Group.READ, Permission.Group.MEMBER_READ): [
        [group_readable_by_world],
        [group_readable_by_members, group_has_user_as_member],
        [group_authority_matches_authenticated_client],
    ],
    Permission.Group.FLAG: [
        # Any logged in user should be able to flag things they can see
        [group_readable_by_world, authenticated],
        [group_readable_by_members, group_has_user_as_member],
    ],
    Permission.Group.ADMIN: [
        [group_authority_matches_authenticated_client],
        [group_created_by_user],
        # Those with the admin or staff Role should be able to admin/edit any
        # group
        [user_is_staff],
        [user_is_admin],
    ],
    Permission.Group.MEMBER_ADD: [[group_authority_matches_authenticated_client]],
    Permission.Group.MODERATE: [[group_created_by_user]],
    Permission.Group.UPSERT: [
        [group_created_by_user],
        [group_not_found, authenticated_user],
    ],
}


def _expand_iterated_keys(mapping):
    """Replace iterable items as keys with repeated keys."""

    multi_value_keys = {}
    for key, value in mapping.items():
        try:
            multi_value_keys[key] = list(key)
        except TypeError:
            continue

    for key, multi_keys in multi_value_keys.items():
        value = mapping.pop(key)

        for new_key in multi_keys:
            mapping[new_key] = value


_expand_iterated_keys(PERMISSION_MAP)


def _duplicate(permission, adding, or_=None):
    return [clause + adding for clause in PERMISSION_MAP[permission]] + (or_ or [])


ANNOTATIONS = {
    # --------------------------------------------------------------------- #
    # Annotations
    Permission.Annotation.CREATE: [[authenticated]],
    # You can be notified about an annotation even if it's been deleted
    Permission.Annotation.READ_REALTIME_UPDATES: _duplicate(
        Permission.Group.READ,
        adding=[annotation_is_shared],
        or_=[[annotation_is_not_shared, annotation_created_by_user]],
    ),
    Permission.Annotation.READ: _duplicate(
        Permission.Group.READ,
        adding=[annotation_not_deleted, annotation_is_shared],
        or_=[
            [
                annotation_not_deleted,
                annotation_is_not_shared,
                annotation_created_by_user,
            ]
        ],
    ),
    Permission.Annotation.FLAG: _duplicate(
        Permission.Group.FLAG,
        adding=[annotation_not_deleted, annotation_is_shared],
        or_=[
            [
                annotation_not_deleted,
                annotation_is_not_shared,
                annotation_created_by_user,
            ]
        ],
    ),
    Permission.Annotation.MODERATE: _duplicate(
        Permission.Group.MODERATE,
        adding=[
            annotation_not_deleted,
            annotation_is_shared,
        ],
    ),
    # The user who created the annotation always has the these permissions
    Permission.Annotation.UPDATE: [
        [annotation_not_deleted, annotation_created_by_user],
    ],
    Permission.Annotation.DELETE: [
        [annotation_not_deleted, annotation_created_by_user]
    ],
}
PERMISSION_MAP.update(ANNOTATIONS)
