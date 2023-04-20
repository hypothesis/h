from h_pyramid_sentry import report_exception

from h.presenters import AnnotationSearchIndexPresenter
from h.services.annotation_read import AnnotationReadService
from h.tasks import indexer


class SearchIndexService:
    """Service for manipulating the search index."""

    # The DB setting that stores whether a full re-index is taking place
    REINDEX_SETTING_KEY = "reindex.new_index"

    def __init__(  # pylint:disable=too-many-arguments
        self,
        request,
        es_client,
        session,
        settings,
        queue,
        annotation_read_service: AnnotationReadService,
    ):
        """
        Create an instance of the service.

        :param request: Pyramid request object
        :param es_client: Elasticsearch client
        :param session: DB session
        :param settings: Instance of settings (or other object with `get()`)
        :param queue: The sync_annotations job queue
        :param annotation_read_service: AnnotationReadService instance
        """
        self._request = request
        self._es = es_client
        self._db = session
        self._settings = settings
        self._queue = queue
        self._annotation_read_service = annotation_read_service

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

    @staticmethod
    def add_annotations_between_times(start_time, end_time, tag):
        """
        Add all annotations between two times to the search index.

        All annotations whose updated time is between the given start_time and
        end_time (inclusive) will be queued for background indexing into
        Elasticsearch.

        :type start_time: datetime.datetime
        :type end_time: datetime.datetime
        """
        indexer.add_annotations_between_times.delay(start_time, end_time, tag)

    @staticmethod
    def add_users_annotations(userid, tag, force=False, schedule_in=None):
        """Add all of a users annotations to the search index."""
        indexer.add_users_annotations.delay(
            userid, tag, force=force, schedule_in=schedule_in
        )

    @staticmethod
    def add_group_annotations(groupid, tag, force=False, schedule_in=None):
        """Add all annotations in a group to the search index."""
        indexer.add_group_annotations.delay(
            groupid, tag, force=force, schedule_in=schedule_in
        )

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
            sync_handler, async_task = self.add_annotation_by_id, indexer.add_annotation
        elif event.action == "delete":
            sync_handler, async_task = (
                self.delete_annotation_by_id,
                indexer.delete_annotation,
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
        """Process `limit` sync_annotation jobs from the job queue."""
        return self._queue.sync(limit)

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
