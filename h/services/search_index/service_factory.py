from h.search.index import BatchIndexer
from h.services.search_index._queue import Queue
from h.services.search_index.service import SearchIndexService


def factory(_context, request):
    """Create a SearchIndexService."""

    return SearchIndexService(
        request=request,
        es_client=request.es,
        session=request.db,
        settings=request.find_service(name="settings"),
        queue=Queue(
            db=request.db,
            es=request.es,
            batch_indexer=BatchIndexer(request.db, request.es, request),
        ),
    )
