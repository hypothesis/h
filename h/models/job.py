from sqlalchemy import Column, DateTime, UnicodeText, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from h.db import Base


class Job(Base):
    """A job in the job queue. See services/job_queue.py for more details."""

    __tablename__ = "job"

    id = Column(UUID, server_default=func.uuid_generate_v1mc(), primary_key=True)
    enqueued_at = Column(DateTime, nullable=False, server_default=func.now())
    scheduled_at = Column(DateTime, nullable=False, server_default=func.now())
    tag = Column(UnicodeText, nullable=False)
    kwargs = Column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
