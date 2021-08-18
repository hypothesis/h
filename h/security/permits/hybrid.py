from enum import Enum

from h.security.permits.predicates import *


class PermissionEnum(Enum):
    def __init__(self, _value, predicates):
        self.predicates = predicates


class Group(PermissionEnum):
    ADMIN = (
        "group:admin",
        [
            [group_authority_matches_authenticated_client],
            [group_created_by_user],
            # Those with the admin or staff Role should be able to admin/edit any
            # group
            [user_is_staff],
            [user_is_admin],
        ],
    )
    JOIN = (
        "group:join",
        [[group_joinable_by_authority, group_matches_user_authority]],
    )
    READ = (
        "group:read",
        [
            [group_readable_by_world],
            [group_readable_by_members, group_has_user_as_member],
            [group_authority_matches_authenticated_client],
        ],
    )
    MEMBER_READ = (
        "group:member:read",
        [
            [group_readable_by_world],
            [group_readable_by_members, group_has_user_as_member],
            [group_authority_matches_authenticated_client],
        ],
    )
    WRITE = (
        "group:write",
        [
            [group_writable_by_authority, group_matches_user_authority],
            [group_writable_by_members, group_has_user_as_member],
        ],
    )
    UPSERT = (
        "group:upsert",
        [
            [group_created_by_user],
            [group_not_found, authenticated_user],
        ],
    )
    CREATE = ("group:create", [[authenticated_user]])
    FLAG = (
        "group:flag",
        [
            # Any logged in user should be able to flag things they can see
            [group_readable_by_world, authenticated],
            [group_readable_by_members, group_has_user_as_member],
        ],
    )
    MODERATE = ("group:moderate", [[group_created_by_user]])
    MEMBER_ADD = (
        "group:member:add",
        [[group_authority_matches_authenticated_client]],
    )


class Annotation(PermissionEnum):
    CREATE = ("annotation:create", [[authenticated]])
    READ = (
        "annotation:read",
        [
            [annotation_live, annotation_not_shared, annotation_created_by_user],
            [annotation_live, annotation_shared, Group.READ],
        ],
    )
    READ_REALTIME_UPDATES = (
        "annotation:read_realtime_updates",
        [
            [annotation_not_shared, annotation_created_by_user],
            [annotation_shared, Group.READ],
        ],
    )
    UPDATE = ("annotation:update", [annotation_live, annotation_created_by_user])
    DELETE = ("annotation:delete", [annotation_live, annotation_created_by_user])
    FLAG = (
        "annotation:flag",
        [
            [annotation_live, annotation_not_shared, annotation_created_by_user],
            [annotation_live, annotation_shared, Group.FLAG],
        ],
    )
    MODERATE = (
        "annotation:moderate",
        [[annotation_live, annotation_shared, Group.MODERATE]],
    )


class Permissions:
    Group = Group
    Annotation = Annotation

    class User(PermissionEnum):
        CREATE = ("user:create", [[authenticated_client]])
        READ = ("user:read", [[user_authority_matches_authenticated_client]])
        UPDATE = ("user:update", [[user_authority_matches_authenticated_client]])

    class Profile(PermissionEnum):
        UPDATE = ("profile:update", [[authenticated_user]])

    class API(PermissionEnum):
        BULK_ACTION = ("api:bulk_action", [[authenticated_client_is_lms]])

    class AdminPage(PermissionEnum):
        ADMINS = ("admin:admins", [[user_is_admin]])
        BADGE = ("admin:badge", [[user_is_admin]])
        FEATURES = ("admin:features", [[user_is_admin]])
        GROUPS = ("admin:groups", [[user_is_admin], [user_is_staff]])
        INDEX = ("admin:index", [[user_is_admin], [user_is_staff]])
        MAILER = ("admin:mailer", [[user_is_admin], [user_is_staff]])
        OAUTH_CLIENTS = ("admin:oauth_clients", [[user_is_admin]])
        ORGANIZATIONS = ("admin:organizations",)
        NIPSA = ("admin:nipsa", [[user_is_admin]])
        SEARCH = ("admin:search", [[user_is_admin]])
        STAFF = ("admin:staff", [[user_is_admin]])
        USERS = ("admin:users", [[user_is_admin], [user_is_staff]])

    def __iter__(self):
        yield self.Group
        yield self.Annotation
        yield self.User
        yield self.Profile
        yield self.API
        yield self.AdminPage

    def predicate_map(self):
        for group in self:
            for permisison in group:
                yield permisison, permisison.predicates
