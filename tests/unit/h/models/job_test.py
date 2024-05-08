from datetime import datetime

from h.models.job import Job


class TestJob:
    def test___repr__(self):
        job = Job(
            id=42,
            name="job_name",
            enqueued_at=datetime(
                year=2024,
                month=5,
                day=8,
                hour=11,
                minute=51,
                second=23,
            ),
            scheduled_at=datetime(
                year=2024,
                month=6,
                day=1,
                hour=0,
                minute=0,
                second=0,
            ),
            expires_at=datetime(
                year=2025,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
            ),
            priority=3,
            tag="job_tag",
            kwargs={"foo": "FOO", "bar": "BAR"},
        )

        assert (
            repr(job)
            == "Job(id=42, name='job_name', enqueued_at=datetime.datetime(2024, 5, 8, 11, 51, 23), scheduled_at=datetime.datetime(2024, 6, 1, 0, 0), expires_at=datetime.datetime(2025, 1, 1, 0, 0), priority=3, tag='job_tag', kwargs={'foo': 'FOO', 'bar': 'BAR'})"
        )
