import hmac
import re

import sqlalchemy as sa

from h.models.auth_client import AuthClient, GrantType


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


def verify_auth_client(client_id, client_secret, db_session):
    """
    Return matching AuthClient or None.

    Attempt to retrieve the :py:class:`h.models.auth_client.AuthClient` record
    indicated by ``client_id`` and ``client_secret`` and perform some validation
    checks on the record.

    Returns ``None`` if retrieval or any checks fail

    :rtype: :py:class:`h.models.auth_client.AuthClient` or ``None``
    """

    # We fetch the client by its ID and then do a constant-time comparison of
    # the secret with that provided in the request.
    #
    # It is important not to include the secret as part of the SQL query
    # because the resulting code may be subject to a timing attack.
    try:  # fetch matching AuthClient record for `client_id`
        client = db_session.query(AuthClient).get(client_id)
    except sa.exc.StatementError:  # query: client_id is malformed
        return None
    if client is None:  # no record returned from query
        return None
    if client.secret is None:  # client is not confidential
        return None
    if client.grant_type != GrantType.client_credentials:  # need these for auth_clients
        return None

    if not hmac.compare_digest(client.secret, client_secret):
        return None

    return client
