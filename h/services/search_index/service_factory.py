from h.services.search_index.service import SearchIndexService


def factory(_context, request):
    """Create a SearchIndexService."""

    return SearchIndexService(
        request=request,
        es_client=request.es,
        session=request.db,
        settings=request.find_service(name="settings"),
    )
