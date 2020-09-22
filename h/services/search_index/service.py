from h import storage
from h.events import AnnotationTransformEvent
from h.presenters import AnnotationSearchIndexPresenter


class SearchIndexService:
    # The DB setting that stores whether a full re-index is taking place
    REINDEX_SETTING_KEY = "reindex.new_index"

    def __init__(self, request, es_client, session, settings):
        self.request = request
        self.es_client = es_client
        self.session = session
        self.settings = settings

    def add_annotation_by_id(self, annotation_id):
        annotation = storage.fetch_annotation(self.session, annotation_id)
        if not annotation:
            return

        self.add_annotation(annotation)

        if annotation.is_reply:
            self.add_annotation_by_id(annotation.thread_root_id)

    def add_annotation(self, annotation):
        """
        Index an annotation into the search index.

        A new annotation document will be created in the search index or,
        if the index already contains an annotation document with the same ID as
        the given annotation then it will be updated.

        :param annotation: the annotation to index

        """
        body = AnnotationSearchIndexPresenter(annotation, self.request).asdict()

        self.request.registry.notify(
            AnnotationTransformEvent(self.request, annotation, body)
        )

        self._index_annotation_body(annotation.id, body, refresh=False)

    def delete_annotation_by_id(self, annotation_id, refresh=False):
        """
        Mark an annotation as deleted in the search index.

        This will write a new body that only contains the ``deleted`` boolean field
        with the value ``true``. It allows us to rely on Elasticsearch to complain
        about dubious operations while re-indexing when we use `op_type=create`.

        :param annotation_id: the annotation id whose corresponding document to
            delete from the search index
        :param refresh: Force this deletion to be immediately visible to search operations
        """

        self._index_annotation_body(annotation_id, {"deleted": True}, refresh=refresh)

    def _index_annotation_body(
        self, annotation_id, body, refresh, target_index=None,
    ):

        self.es_client.conn.index(
            index=self.es_client.index if target_index is None else target_index,
            doc_type=self.es_client.mapping_type,
            body=body,
            id=annotation_id,
            refresh=refresh,
        )

        if target_index is not None:
            return

        future_index = self.settings.get(self.REINDEX_SETTING_KEY)
        if future_index:
            self._index_annotation_body(
                annotation_id, body, refresh, target_index=future_index,
            )


def factory(_context, request):
    return SearchIndexService(
        request=request,
        es_client=request.es,
        session=request.db,
        settings=request.find_service(name="settings"),
    )
