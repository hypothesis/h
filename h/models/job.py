"""
A simple transactional job queue.

This home-grown job queue differs from our Celery task queue in a few ways:

1. The job queue is stored in Postgres so jobs can be added as part of a
   Postgres transaction.

   For example a new annotation can be added to the annotations table and a job
   to synchronize that annotation into Elasticsearch can be added to the job
   queue as part of the same Postgres transaction. This way it's not possible
   to add an annotation to Postgres and fail to add it to the job queue or
   vice-versa. The two can't get out of sync because they're part of a single
   Postgres transaction.

2. The job queue is less immediate.

   Jobs are processed in batch by periodic Celery tasks that run every N
   minutes so a job added to the job queue might not get processed until N
   minutes later (or even longer: if the job queue is currently long then the
   periodic task may have to run multiple times before it gets to your job).

   Tasks added to Celery can be processed by a worker almost immediately.

3. The job queue is very simple and has far fewer features than Celery.

   Celery should be the default task queue for almost all tasks, and only jobs
   that really need Postgres transactionality should use this custom job queue.
"""
from sqlalchemy import Column, DateTime, Integer, Sequence, UnicodeText, func, text
from sqlalchemy.dialects.postgresql import JSONB

from h.db import Base


class Job(Base):
    """A job in the job queue."""

    __tablename__ = "job"

    id = Column(Integer, Sequence("job_id_seq", cycle=True), primary_key=True)
    name = Column(UnicodeText, nullable=False)
    enqueued_at = Column(DateTime, nullable=False, server_default=func.now())
    scheduled_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(
        DateTime, nullable=False, server_default=text("now() + interval '30 days'")
    )
    priority = Column(Integer, nullable=False)
    tag = Column(UnicodeText, nullable=False)
    kwargs = Column(
        JSONB,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
