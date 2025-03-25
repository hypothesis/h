"""
Mixins for use with model classes that use SQLAlchemy's dataclasses integration.

See: https://docs.sqlalchemy.org/en/20/orm/dataclasses.html
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column


class AutoincrementingIntegerID(MappedAsDataclass):
    id: Mapped[int] = mapped_column(
        init=False, primary_key=True, autoincrement=True, sort_order=-100
    )


class Timestamps(MappedAsDataclass):
    created: Mapped[datetime] = mapped_column(
        init=False,
        repr=False,
        server_default=func.now(),
        sort_order=-10,
        nullable=False,
    )
    updated: Mapped[datetime] = mapped_column(
        init=False,
        repr=False,
        server_default=func.now(),
        onupdate=func.now(),
        sort_order=-10,
        nullable=False,
    )
