def includeme(config):
    """Include the annotator-store API."""
    config.include('h.api.store')
    config.include('h.api.token')
