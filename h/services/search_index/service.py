from h.events import AnnotationTransformEvent
from h.presenters import AnnotationSearchIndexPresenter


class SearchIndexService:
    def __init__(self, es_client, request):
        self.es_client = es_client
        self.request = request

    def add_annotation(self, annotation, target_index=None):
        return _add_annotation(
            self.es_client, annotation, self.request, target_index=target_index
        )

    def delete_annotation_by_id(self, annotation_id, target_index=None, refresh=False):
        return _delete_annotation(self.es_client, annotation_id, target_index, refresh)


def factory(_context, request):
    return SearchIndexService(request.es, request)


def _add_annotation(es, annotation, request, target_index=None):
    """
    Index an annotation into the search index.

    A new annotation document will be created in the search index or,
    if the index already contains an annotation document with the same ID as
    the given annotation then it will be updated.

    :param es: the Elasticsearch client object to use
    :type es: h.search.Client

    :param annotation: the annotation to index
    :type annotation: h.models.Annotation

    :param target_index: the index name, uses default index if not given
    :type target_index: unicode
    """
    as_dict = AnnotationSearchIndexPresenter(annotation, request).asdict()

    request.registry.notify(AnnotationTransformEvent(request, annotation, as_dict))

    if target_index is None:
        target_index = es.index

    es.conn.index(
        index=target_index, doc_type=es.mapping_type, body=as_dict, id=annotation.id
    )


def _delete_annotation(es, annotation_id, target_index=None, refresh=False):
    """
    Mark an annotation as deleted in the search index.

    This will write a new body that only contains the ``deleted`` boolean field
    with the value ``true``. It allows us to rely on Elasticsearch to complain
    about dubious operations while re-indexing when we use `op_type=create`.

    :param es: the Elasticsearch client object to use
    :type es: h.search.Client

    :param annotation_id: the annotation id whose corresponding document to
        delete from the search index
    :type annotation_id: str

    :param target_index: the index name, uses default index if not given
    :type target_index: unicode

    :param refresh: Force this deletion to be immediately visible to search operations
    :type refresh: bool

    """

    if target_index is None:
        target_index = es.index

    es.conn.index(
        index=target_index,
        doc_type=es.mapping_type,
        body={"deleted": True},
        id=annotation_id,
        refresh=refresh,
    )
