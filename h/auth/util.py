import re


def default_authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return request.registry.settings.get("h.authority", request.domain)


def client_authority(request):
    """
    Return the authority associated with an authenticated auth_client or None.

    Once a request with an auth_client is authenticated, a principal is set
    indicating the auth_client's verified authority

    see :func:`~h.auth.util.principals_for_auth_client` for more details on
    principals applied when auth_clients are authenticated

    :rtype: str or None
    """
    for principal in request.effective_principals:
        match = re.match(r"^client_authority:(.+)$", principal)
        if match and match.group(1):
            return match.group(1)

    return None
