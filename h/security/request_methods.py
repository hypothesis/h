def default_authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return request.registry.settings.get("h.authority", request.domain)


def includeme(config):  # pragma: no cover
    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, reify=True)
