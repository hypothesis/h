def client_authority(request):
    """
    Return the authority associated with an authenticated auth_client or None.

    :rtype: str or None
    """
    if request.identity and request.identity.auth_client:
        return request.identity.auth_client.authority

    return None
