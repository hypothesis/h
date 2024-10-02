from enum import Enum


class Permission:
    """
    A collection of permission enumerations.

    These are generally used in the code as `Permission.Group.READ`. So if you
    need to search for uses of these that's a good thing to grep for.

    As these are `Enum`s they _should not_ compare equal to the string values
    inside them. These strings may change without notice, but comparing with
    the `Enum` object should always be safe.
    """

    class Group(Enum):
        """Permissions relating to groups."""

        READ = "group:read"
        """See annotations in this group."""

        WRITE = "group:write"
        """Create annotations in this group."""

        CREATE = "group:create"
        """Create a new group."""

        EDIT = "group:edit"
        """Update the details of a group."""

        FLAG = "group:flag"
        """Mark annotations in this group as inappropriate for moderators."""

        MODERATE = "group:moderate"
        """Hide or unhide annotations in this group as a moderator."""

        JOIN = "group:join"
        """Join a group."""

        MEMBER_ADD = "group:member:add"
        """Add a user other than yourself (that's JOIN) to a group."""

    class Annotation(Enum):
        """Permissions relating to annotations."""

        READ = "annotation:read"
        """See the content of an annotation."""

        READ_REALTIME_UPDATES = "annotation:read_realtime_updates"
        """Be notified of changes to an annotation via Websocket."""

        UPDATE = "annotation:update"
        """Update an annotation."""

        CREATE = "annotation:create"
        """Create an annotation."""

        DELETE = "annotation:delete"
        """Delete an annotation."""

        FLAG = "annotation:flag"
        """Mark an annotation as inappropriate for moderators."""

        MODERATE = "annotation:moderate"
        """Hide or unhide an annotation as a moderator."""

    class User(Enum):
        """
        Permissions for operating on users other than yourself.

        For permissions relating to changing the logged in user see `Profile`.
        This is used by authenticated clients to modify users.
        """

        READ = "user:read"
        """Read user details."""

        CREATE = "user:create"
        """Create a user."""

        UPDATE = "user:update"
        """Update a user."""

    class Profile(Enum):
        """Permissions for operating on your own data as a logged in user."""

        UPDATE = "profile:update"
        """Users updating their own profile."""

    class AdminPage(Enum):
        """Permissions for admin page actions."""

        HIGH_RISK = "admin:high_risk"
        """
        Admins performing high risk admin activities.

        This involves scary operations which might be irreversible.
        """

        LOW_RISK = "admin:low_risk"
        """Admins performing low risk admin activities."""

    class API(Enum):
        """Permissions for usage restricted portions of the API."""

        BULK_ACTION = "api:bulk_action"
        """Calling the /bulk/api end-point. Currently used by LMS."""
