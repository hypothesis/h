from h.search.index import BatchIndexer
from h.services import AnnotationService
from h.services.search_index._queue import Queue
from h.services.search_index.service import SearchIndexService


def factory(_context, request):
    """Create a SearchIndexService."""

    return SearchIndexService(
        request=request,
        es_client=request.es,
        session=request.db,
        settings=request.find_service(name="settings"),
        annotation_service=request.find_service(AnnotationService),
        queue=Queue(
            db=request.db,
            es=request.es,
            batch_indexer=BatchIndexer(request.db, request.es, request),
        ),
    )
