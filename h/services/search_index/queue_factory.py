"""The service factory for the search_index.queue service."""
from h.search.index import BatchIndexer
from h.services.search_index.queue import Queue


def factory(_context, request):
    """Return the search_index.queue service."""
    return Queue(
        db=request.db,
        es=request.es,
        batch_indexer=BatchIndexer(request.db, request.es, request),
    )
