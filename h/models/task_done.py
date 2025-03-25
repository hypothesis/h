from datetime import datetime

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, MappedAsDataclass
from sqlalchemy.testing.schema import mapped_column

from h.db import Base
from h.db.mixins import Timestamps
from h.db.mixins_dataclasses import AutoincrementingIntegerID


class TaskDone(Base, AutoincrementingIntegerID, Timestamps, MappedAsDataclass):
    __tablename__ = "task_done"

    expires_at: Mapped[datetime] = mapped_column(
        init=False, nullable=False, server_default=text("now() + interval '30 days'")
    )
    data: Mapped[dict] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
