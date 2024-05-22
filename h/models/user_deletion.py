from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from h.db import Base
from h.models import helpers


class UserDeletion(Base):
    """A record of a user account that was deleted."""

    __tablename__ = "user_deletion"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    userid: Mapped[str]
    """The userid of the user who was deleted."""

    requested_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),  # pylint:disable=not-callable
    )
    """The time at which the user deletion was requested."""

    requested_by: Mapped[str]
    """The userid of the user who requested the deletion."""

    tag: Mapped[str]
    """Just a string 'tag' field.

    For example different views that delete users might put different tag
    values here.
    """

    registered_date: Mapped[datetime]
    """The time when the deleted user account was first registered."""

    num_annotations: Mapped[int]
    """The number of annotations that the deleted user account had."""

    def __repr__(self) -> str:
        return helpers.repr_(
            self,
            [
                "id",
                "userid",
                "requested_at",
                "requested_by",
                "tag",
                "registered_date",
                "num_annotations",
            ],
        )
