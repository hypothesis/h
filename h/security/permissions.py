class Permission:
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
