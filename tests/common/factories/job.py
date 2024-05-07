import datetime

from factory import Faker, LazyAttribute, LazyFunction, SubFactory

from h import models
from h.db.types import URLSafeUUID

from .annotation import Annotation
from .base import ModelFactory
from .user import User


class Job(ModelFactory):
    class Meta:
        model = models.Job

    name = "test_job"
    priority = Faker("random_element", elements=[1, 100, 1000, 10000])
    tag = "test_tag"


class SyncAnnotationJob(Job):
    """
    A factory for creating "sync_annotation" jobs.

    By default this creates jobs with job.name="sync_annotation", with a
    scheduled_at time in the past, and with a job.kwargs that contains an
    annotation_id and force=False.

    By default a new annotation will be created for the job to use.
    The annotation will exist in the DB but will *not* be in
    Elasticsearch -- tests must index the annotation themselves if they want it
    to be in Elasticsearch.
    """

    class Meta:
        exclude = ("annotation", "force")

    annotation = SubFactory(Annotation)
    force = False

    name = "sync_annotation"
    scheduled_at = LazyFunction(
        lambda: datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    )
    kwargs = LazyAttribute(
        lambda o: {
            "annotation_id": URLSafeUUID.url_safe_to_hex(o.annotation.id),
            "force": o.force,
        }
    )


class ExpungeUserJob(Job):
    class Meta:
        exclude = "user"

    user = SubFactory(User)

    name = "expunge_user"
    kwargs = LazyAttribute(lambda o: {"userid": o.user.userid})
