def default_authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return request.registry.settings.get("h.authority", request.domain)


def effective_authority(request):
    """
    Return the authority associated with an request.

    This will try the auth client first, then will return the results of
    `default_authority()`.
    """
    if request.identity and request.identity.auth_client:
        return request.identity.auth_client.authority

    # We could call the method directly here, but instead we'll go through the
    # request method attached below. This allows us to benefit from caching
    # if the method has been called before. Also if the request method ever
    # points to a new function, we don't have to update.
    return request.default_authority


def includeme(config):  # pragma: no cover
    # Allow retrieval of the authority from the request object.
    config.add_request_method(default_authority, reify=True)
    config.add_request_method(effective_authority, reify=True)
