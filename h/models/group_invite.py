from datetime import datetime
from functools import partial

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship

from h.db import Base
from h.db.dataclasses_mixins import AutoincrementingIntegerID, Timestamps
from h.models.group import GROUP_MEMBERSHIP_ROLES_CHECK_CONSTRAINT
from h.pubid import generate


class GroupInvite(Base, AutoincrementingIntegerID, Timestamps, MappedAsDataclass):
    __tablename__ = "group_invite"

    pubid: Mapped[str] = mapped_column(unique=True, default_factory=partial(generate, 12), init=False)  # fmt: skip
    roles: Mapped[list] = mapped_column(JSONB, GROUP_MEMBERSHIP_ROLES_CHECK_CONSTRAINT)
    expires: Mapped[datetime]

    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), init=False)
    group: Mapped["Group"] = relationship()  # noqa: F821

    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), init=False)
    user: Mapped["User"] = relationship(foreign_keys=[user_id])  # noqa: F821

    creator_id: Mapped[int] = mapped_column(ForeignKey("user.id"), init=False)
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id])  # noqa: F821
