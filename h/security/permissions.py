from enum import Enum


class Permission:
    class Group(Enum):
        EDIT = "group:edit"
        JOIN = "group:join"
        READ = "group:read"
        WRITE = "group:write"
        UPSERT = "group:upsert"
        CREATE = "group:create"
        FLAG = "group:flag"
        MODERATE = "group:moderate"
        MEMBER_READ = "group:member:read"
        MEMBER_ADD = "group:member:add"

    class Annotation(Enum):
        READ = "annotation:read"
        READ_REALTIME_UPDATES = "annotation:read_realtime_updates"
        UPDATE = "annotation:update"
        CREATE = "annotation:create"
        DELETE = "annotation:delete"
        FLAG = "annotation:flag"
        MODERATE = "annotation:moderate"

    class User(Enum):
        READ = "user:read"
        CREATE = "user:create"
        UPDATE = "user:update"

    class Profile(Enum):
        UPDATE = "profile:update"

    class AdminPage(Enum):
        HIGH_RISK = "admin:high_risk"
        LOW_RISK = "admin:low_risk"

    class API(Enum):
        BULK_ACTION = "api:bulk_action"
