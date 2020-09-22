from h.events import AnnotationTransformEvent
from h.presenters import AnnotationSearchIndexPresenter


class SearchIndexService:
    def __init__(self, es_client, request):
        self.es_client = es_client
        self.request = request

    def add_annotation(self, annotation, target_index=None):
        """
        Index an annotation into the search index.

        A new annotation document will be created in the search index or,
        if the index already contains an annotation document with the same ID as
        the given annotation then it will be updated.

        :param annotation: the annotation to index
        :param target_index: the index name, uses default index if not given
        """
        body = AnnotationSearchIndexPresenter(annotation, self.request).asdict()

        self.request.registry.notify(
            AnnotationTransformEvent(self.request, annotation, body)
        )

        self._index_annotation_body(annotation.id, body, target_index)

    def delete_annotation_by_id(self, annotation_id, target_index=None, refresh=False):
        """
        Mark an annotation as deleted in the search index.

        This will write a new body that only contains the ``deleted`` boolean field
        with the value ``true``. It allows us to rely on Elasticsearch to complain
        about dubious operations while re-indexing when we use `op_type=create`.

        :param annotation_id: the annotation id whose corresponding document to
            delete from the search index
        :param target_index: the index name, uses default index if not given
        :param refresh: Force this deletion to be immediately visible to search operations
        """

        self._index_annotation_body(
            annotation_id, {"deleted": True}, target_index, refresh
        )

    def _index_annotation_body(self, annotation_id, body, target_index, refresh=False):
        self.es_client.conn.index(
            index=self.es_client.index if target_index is None else target_index,
            doc_type=self.es_client.mapping_type,
            body=body,
            id=annotation_id,
            refresh=refresh,
        )


def factory(_context, request):
    return SearchIndexService(request.es, request)
