from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from h.db import Base


class UserRename(Base):
    """An audit record of a user rename."""

    __tablename__ = "user_rename"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL")
    )

    old_userid: Mapped[str]
    """The userid of the user before the renaming."""

    new_userid: Mapped[str]
    """The userid of the user after the renaming."""

    requested_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    """The time at which the user rename was requested."""

    requested_by: Mapped[str]
    """The userid of the user who requested the rename."""

    tag: Mapped[str]
    """Just a string 'tag' field.

    For example different views that renemae users might put different tag
    values here.
    """
