import datetime

from h.models import Job


def test__repr__(db_session):
    job = Job(
        enqueued_at=datetime.datetime(1970, 1, 1),
        scheduled_at=datetime.datetime(1980, 2, 2),
        tag="foo",
        kwargs={"bar": "gar"},
    )
    db_session.add(job)
    db_session.flush()

    assert (
        repr(job)
        == f"Job(id={job.id}, enqueued_at=1970-01-01 00:00:00, scheduled_at=1980-02-02 00:00:00, tag=foo, kwargs={{'bar': 'gar'}})"
    )
