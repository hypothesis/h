def includeme(config):
    """Include the annotator-store API."""
    # Order matters here, in case the token and store routes share a prefix
    config.include('h.api.token')
    config.include('h.api.store')
