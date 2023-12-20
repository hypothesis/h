from collections import defaultdict
from datetime import datetime

from sqlalchemy import func

from h.models import Job


class JobQueueMetrics:
    """A service for generating metrics about the job queue."""

    def __init__(self, db):
        self._db = db

    def metrics(self):
        """
        Return a list of New Relic-style metrics about the job queue.

        The returned list of metrics is suitable for passing to
        newrelic.agent.record_custom_metrics().
        """
        metrics = defaultdict(int)
        now = datetime.utcnow()

        # Expired jobs.
        metrics["Custom/JobQueue/Count/Expired"] = (
            self._db.query(Job).filter(Job.expires_at < now).count()
        )

        # Unexpired jobs by tag and name.
        name_tags = (
            self._db.query(Job.name, Job.tag, func.count())
            .filter(Job.expires_at >= now)
            .group_by(Job.name)
            .group_by(Job.tag)
            .distinct()
        )
        for name, tag, count in name_tags:
            metrics[f"Custom/JobQueue/Count/Name/{name}/Tag/{tag}"] = count
            metrics[f"Custom/JobQueue/Count/Name/{name}/Total"] += count

        # Unexpired jobs by priority.
        priority_counts = (
            self._db.query(Job.priority, func.count())
            .filter(Job.expires_at >= now)
            .group_by(Job.priority)
        )

        for priority, count in priority_counts:
            metrics[f"Custom/JobQueue/Count/Priority/{priority}"] = count

        # Total unexpired jobs.
        metrics["Custom/JobQueue/Count/Total"] = sum(
            count for _, count in priority_counts
        )

        return metrics.items()


def factory(_context, request):
    return JobQueueMetrics(request.db)
