from h import storage
from h.events import AnnotationTransformEvent
from h.presenters import AnnotationSearchIndexPresenter


class SearchIndexService:
    """Service for manipulating the search index."""

    # The DB setting that stores whether a full re-index is taking place
    REINDEX_SETTING_KEY = "reindex.new_index"

    def __init__(self, request, es_client, session, settings):
        """
        Create an instance of the service.

        :param request: Pyramid request object
        :param es_client: Elasticsearch client
        :param session: DB session
        :param settings: Instance of settings (or other object with `get()`)
        """
        self._request = request
        self._es = es_client
        self._db = session
        self._settings = settings

    def add_annotation_by_id(self, annotation_id):
        """
        Add an annotation into the search index by id.

        A new annotation document will be created in the search index or,
        if the index already contains an annotation document with the same Id
        as the given annotation then it will be updated.

        If no annotation is found, nothing happens.

        :param annotation_id: Id of the annotation to add.
        """
        annotation = storage.fetch_annotation(self._db, annotation_id)
        if not annotation:
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
        body = AnnotationSearchIndexPresenter(annotation, self._request).asdict()

        self._request.registry.notify(
            AnnotationTransformEvent(self._request, annotation, body)
        )

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

    def _index_annotation_body(
        self, annotation_id, body, refresh, target_index=None,
    ):

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
                annotation_id, body, refresh, target_index=future_index,
            )
