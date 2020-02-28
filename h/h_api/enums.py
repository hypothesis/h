"""All enumerations used in h_api."""

from enum import Enum


class DataType(Enum):
    """Types of data we exchange."""

    USER = "user"
    GROUP = "group"
    GROUP_MEMBERSHIP = "group_membership"


class CommandType(Enum):
    """BulkAPI command types."""

    CONFIGURE = "configure"
    UPSERT = "upsert"
    CREATE = "create"
