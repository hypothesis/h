from collections import defaultdict

from dateutil.parser import isoparse
from h_pyramid_sentry import report_exception

from h import tasks
from h.db.types import URLSafeUUID
from h.models import Annotation
from h.presenters import AnnotationSearchIndexPresenter
from h.search.index import BatchIndexer
from h.services.annotation_read import AnnotationReadService


class Result:
    """String values for logging and metrics."""

    # These are in the style of New Relic custom metric names.
    SYNCED_MISSING = "Synced/{tag}/Missing_from_Elastic"
    SYNCED_DIFFERENT = "Synced/{tag}/Different_in_Elastic"
    SYNCED_FORCED = "Synced/{tag}/Forced"
    SYNCED_TAG_TOTAL = "Synced/{tag}/Total"
    SYNCED_TOTAL = "Synced/Total"
    COMPLETED_UP_TO_DATE = "Completed/{tag}/Up_to_date_in_Elastic"
    COMPLETED_DELETED = "Completed/{tag}/Deleted_from_db"
    COMPLETED_FORCED = "Completed/{tag}/Forced"
    COMPLETED_TAG_TOTAL = "Completed/{tag}/Total"
    COMPLETED_TOTAL = "Completed/Total"


class SearchIndexService:
    """Service for manipulating the search index."""

    # The DB setting that stores whether a full re-index is taking place
    REINDEX_SETTING_KEY = "reindex.new_index"

    def __init__(  # pylint:disable=too-many-arguments
        self,
        request,
        es,
        db,
        settings,
        annotation_read_service: AnnotationReadService,
        batch_indexer,
        queue_service,
    ):
        """
        Create an instance of the service.

        :param request: Pyramid request object
        :param es: Elasticsearch client
        :param db: DB session
        :param settings: Instance of settings (or other object with `get()`)
        :param annotation_read_service: AnnotationReadService instance
        """
        self._request = request
        self._es = es
        self._db = db
        self._settings = settings
        self._annotation_read_service = annotation_read_service
        self._batch_indexer = batch_indexer
        self._queue_service = queue_service

    def add_annotation_by_id(self, annotation_id):
        """
        Add an annotation into the search index by id.

        A new annotation document will be created in the search index or,
        if the index already contains an annotation document with the same Id
        as the given annotation then it will be updated.

        If no annotation is found, nothing happens.

        :param annotation_id: Id of the annotation to add.
        """
        annotation = self._annotation_read_service.get_annotation_by_id(annotation_id)
        if not annotation or annotation.deleted:
            return

        self.add_annotation(annotation)

        if annotation.is_reply:
            self.add_annotation_by_id(annotation.thread_root_id)

    def add_annotation(self, annotation):
        """
        Add an annotation into the search index.

        A new annotation document will be created in the search index or,
        if the index already contains an annotation document with the same Id
        as the given annotation then it will be updated.

        :param annotation: Annotation object to index
        """
        if annotation.deleted:
            return

        body = AnnotationSearchIndexPresenter(annotation, self._request).asdict()

        self._index_annotation_body(annotation.id, body, refresh=False)

    def delete_annotation_by_id(self, annotation_id, refresh=False):
        """
        Mark an annotation as deleted in the search index.

        This will write a new body that only contains the `deleted` boolean
        field with the value `true`. It allows us to rely on Elasticsearch to
        complain about dubious operations while re-indexing when we use
        `op_type=create`.

        :param annotation_id: Annotation id whose corresponding document to
            delete from the search index
        :param refresh: Force this deletion to be immediately visible to search
            operations
        """

        self._index_annotation_body(annotation_id, {"deleted": True}, refresh=refresh)

    def handle_annotation_event(self, event):
        """
        Process an annotation event, taking appropriate action to the event.

        This will attempt to fulfill the request synchronously if asked, or
        fall back on a delayed celery task if not or if this fails.

        :param event: AnnotationEvent object
        """
        if event.action in ["create", "update"]:
            sync_handler, async_task = (
                self.add_annotation_by_id,
                tasks.indexer.add_annotation,
            )
        elif event.action == "delete":
            sync_handler, async_task = (
                self.delete_annotation_by_id,
                tasks.indexer.delete_annotation,
            )
        else:
            return False

        try:
            return sync_handler(event.annotation_id)

        except Exception as err:  # pylint: disable=broad-except
            report_exception(err)

        # Either the synchronous method was disabled, or failed...
        return async_task.delay(event.annotation_id)

    def sync(self, limit):
        """
        Synchronize a batch of annotations from Postgres to Elasticsearch.

        Called periodically by a Celery task (see h-periodic).

        Each time this method runs it considers a fixed number of sync
        annotation jobs from the queue and for each job:

        * If the annotation is already the same in Elastic as in the DB then
          remove the job from the queue

        * If the annotation is missing from Elastic or different in Elastic
          than in the DB then re-sync the annotation into Elastic. Leave the
          job on the queue to be re-checked and removed the next time the
          method runs.
        """
        jobs = self._queue_service.get(name="sync_annotation", limit=limit)

        if not jobs:
            return {}

        counts = defaultdict(set)

        annotation_ids = {
            URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
            for job in jobs
            if not job.kwargs.get("force", False)
        }
        if annotation_ids:
            annotations_from_db = self._get_annotations_from_db(annotation_ids)
            annotations_from_es = self._get_annotations_from_es(annotation_ids)
        else:
            annotations_from_db = {}
            annotations_from_es = {}

        # Completed jobs that can be removed from the queue.
        job_complete = []

        # IDs of annotations to (re-)add to Elasticsearch because they're
        # either missing from Elasticsearch or are different in Elasticsearch
        # than in the DB.
        annotation_ids_to_sync = set()

        for job in jobs:
            annotation_id = URLSafeUUID.hex_to_url_safe(job.kwargs["annotation_id"])
            annotation_from_db = annotations_from_db.get(annotation_id)
            annotation_from_es = annotations_from_es.get(annotation_id)

            if job.kwargs.get("force", False):
                annotation_ids_to_sync.add(annotation_id)
                job_complete.append(job)
                counts[Result.SYNCED_FORCED.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TOTAL].add(annotation_id)
                counts[Result.COMPLETED_FORCED.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TOTAL].add(job.id)
            elif not annotation_from_db:
                job_complete.append(job)
                counts[Result.COMPLETED_DELETED.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TOTAL].add(job.id)
            elif not annotation_from_es:
                annotation_ids_to_sync.add(annotation_id)
                counts[Result.SYNCED_MISSING.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TOTAL].add(annotation_id)
            elif not self._equal(annotation_from_es, annotation_from_db):
                annotation_ids_to_sync.add(annotation_id)
                counts[Result.SYNCED_DIFFERENT.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TAG_TOTAL.format(tag=job.tag)].add(annotation_id)
                counts[Result.SYNCED_TOTAL].add(annotation_id)
            else:
                job_complete.append(job)
                counts[Result.COMPLETED_UP_TO_DATE.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TAG_TOTAL.format(tag=job.tag)].add(job.id)
                counts[Result.COMPLETED_TOTAL].add(job.id)

        self._queue_service.delete(job_complete)

        if annotation_ids_to_sync:
            self._batch_indexer.index(list(annotation_ids_to_sync))

        return {key: len(value) for key, value in counts.items()}

    @staticmethod
    def _equal(annotation_from_es, annotation_from_db):
        """Test if the annotations are equal."""
        return (
            annotation_from_es["updated"] == annotation_from_db.updated
            and annotation_from_es["user"] == annotation_from_db.userid
        )

    def _get_annotations_from_db(self, annotation_ids):
        return {
            annotation.id: annotation
            for annotation in self._db.query(
                Annotation.id, Annotation.updated, Annotation.userid
            )
            .filter_by(deleted=False)
            .filter(Annotation.id.in_(annotation_ids))
        }

    def _get_annotations_from_es(self, annotation_ids):
        hits = self._es.conn.search(
            body={
                "_source": ["updated", "user"],
                "query": {"ids": {"values": list(annotation_ids)}},
                "size": len(annotation_ids),
            },
            index=self._es.index,
        )["hits"]["hits"]

        for hit in hits:
            updated = hit["_source"].get("updated")
            updated = isoparse(updated).replace(tzinfo=None) if updated else None
            hit["_source"]["updated"] = updated

        return {hit["_id"]: hit["_source"] for hit in hits}

    def _index_annotation_body(self, annotation_id, body, refresh, target_index=None):
        self._es.conn.index(
            index=self._es.index if target_index is None else target_index,
            doc_type=self._es.mapping_type,
            body=body,
            id=annotation_id,
            refresh=refresh,
        )

        if target_index is not None:
            return

        future_index = self._settings.get(self.REINDEX_SETTING_KEY)
        if future_index:
            self._index_annotation_body(
                annotation_id, body, refresh, target_index=future_index
            )


def factory(_context, request):
    """Create a SearchIndexService."""

    return SearchIndexService(
        request=request,
        es=request.es,
        db=request.db,
        settings=request.find_service(name="settings"),
        annotation_read_service=request.find_service(AnnotationReadService),
        batch_indexer=BatchIndexer(request.db, request.es, request),
        queue_service=request.find_service(name="queue_service"),
    )
