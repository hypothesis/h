from enum import Enum


class Permission(Enum):
    GROUP_ADMIN = "group:admin"  # Is this really "EDIT" or a combination?
    GROUP_JOIN = "group:join"
    GROUP_READ = "group:read"
    GROUP_WRITE = "group:write"
    GROUP_UPSERT = "group:upsert"
    GROUP_CREATE = "group:create"
    GROUP_FLAG = "group:flag"
    GROUP_MODERATE = "group:moderate"
    GROUP_MEMBER_READ = "group:member:read"
    GROUP_MEMBER_ADD = "group:member:add"

    ANNOTATION_ADMIN = "annotation:admin"  # Is this used anywhere?
    ANNOTATION_READ = "annotation:read"
    ANNOTATION_WRITE = "annotation:write"  # Is this granted anywhere?
    ANNOTATION_UPDATE = "annotation:update"
    ANNOTATION_CREATE = "annotation:create"
    ANNOTATION_DELETE = "annotation:delete"
    ANNOTATION_FLAG = "annotation:flag"
    ANNOTATION_MODERATE = "annotation:moderate"

    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"

    PROFILE_UPDATE = "profile:update"

    ADMINPAGE_ADMINS = "admin:admins"
    ADMINPAGE_BADGE = "admin:badge"
    ADMINPAGE_FEATURES = "admin:features"
    ADMINPAGE_GROUPS = "admin:groups"
    ADMINPAGE_INDEX = "admin:index"
    ADMINPAGE_MAILER = "admin:mailer"
    ADMINPAGE_OAUTH_CLIENTS = "admin:oauth_clients"
    ADMINPAGE_ORGANIZATIONS = "admin:organizations"
    ADMINPAGE_NIPSA = "admin:nipsa"
    ADMINPAGE_SEARCH = "admin:search"
    ADMINPAGE_STAFF = "admin:staff"
    ADMINPAGE_USERS = "admin:users"

    API_BULK_ACTION = "api:bulk_action"
