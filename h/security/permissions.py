class Permission:
    class Group:
        ADMIN = "group:admin"  # Is this really "EDIT" or a combination?
        JOIN = "group:join"
        READ = "group:read"
        WRITE = "group:write"
        UPSERT = "group:upsert"
        CREATE = "group:create"
        FLAG = "group:flag"
        MODERATE = "group:moderate"
        MEMBER_READ = "group:member:read"
        MEMBER_ADD = "group:member:add"

    class Annotation:
        READ = "annotation:read"
        UPDATE = "annotation:update"
        CREATE = "annotation:create"
        DELETE = "annotation:delete"
        FLAG = "annotation:flag"
        MODERATE = "annotation:moderate"

    class User:
        READ = "user:read"
        CREATE = "user:create"
        UPDATE = "user:update"

    class Profile:
        UPDATE = "profile:update"

    class AdminPage:
        ADMINS = "admin:admins"
        BADGE = "admin:badge"
        FEATURES = "admin:features"
        GROUPS = "admin:groups"
        INDEX = "admin:index"
        MAILER = "admin:mailer"
        OAUTH_CLIENTS = "admin:oauth_clients"
        ORGANIZATIONS = "admin:organizations"
        NIPSA = "admin:nipsa"
        SEARCH = "admin:search"
        STAFF = "admin:staff"
        USERS = "admin:users"

    class API:
        BULK_ACTION = "api:bulk_action"
