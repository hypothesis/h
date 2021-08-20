def default_authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return request.registry.settings.get("h.authority", request.domain)


def client_authority(request):
    """
    Return the authority associated with an authenticated auth_client or None.

    :rtype: str or None
    """
    # This function is kind of dumb and should be removed...
    if request.identity and request.identity.auth_client:
        return request.identity.auth_client.authority

    return None
