# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re

import hmac

import sqlalchemy as sa
from pyramid import security

from h.auth import role
from h._compat import text_type
from h.models.auth_client import GrantType, AuthClient


def groupfinder(userid, request):
    """
    Return the list of additional principals for a userid, or None.

    This loads the user and then calls ``principals_for_user``.

    If `userid` identifies a valid user in the system, this function will
    return the list of additional principals for that user. If `userid` is not
    recognised as a valid user in the system, the function will return None.

    :param userid: the userid claimed by the request.
    :type userid: str
    :param request: the request object
    :type request: pyramid.request.Request

    :returns: additional principals for the user (possibly empty) or None
    :rtype: list or None
    """
    user_service = request.find_service(name="user")
    user = user_service.fetch(userid)

    return principals_for_user(user)


def principals_for_user(user):
    """Return the list of additional principals for a user, or None."""
    if user is None:
        return None

    principals = set()
    principals.add(role.User)
    if user.admin:
        principals.add(role.Admin)
    if user.staff:
        principals.add(role.Staff)
    for group in user.groups:
        principals.add("group:{group.pubid}".format(group=group))
    principals.add("authority:{authority}".format(authority=user.authority))

    return list(principals)


def translate_annotation_principals(principals):
    """
    Translate a list of annotation principals to a list of pyramid principals.
    """
    result = set([])
    for principal in principals:
        # Ignore suspicious principals from annotations
        if principal.startswith("system."):
            continue
        if principal == "group:__world__":
            result.add(security.Everyone)
        else:
            result.add(principal)
    return list(result)


def default_authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return text_type(request.registry.settings.get("h.authority", request.domain))


def client_authority(request):
    """
    Return the authority associated with an authenticated auth_client or None

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
    Return matching AuthClient or None

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


def principals_for_auth_client(client):
    """
    Return the list of additional principals for an auth client

    :type client: :py:class:`h.models.auth_client.AuthClient`
    :rtype: list
    """

    principals = set([])

    principals.add(
        "client:{client_id}@{authority}".format(
            client_id=client.id, authority=client.authority
        )
    )
    principals.add("client_authority:{authority}".format(authority=client.authority))
    principals.add(role.AuthClient)

    return list(principals)


def principals_for_auth_client_user(user, client):
    """
    Return a union of client and user principals for forwarded user

    :type user: :py:class:`h.models.user.User`
    :type client: :py:class:`h.models.auth_client.AuthClient`
    :rtype: list
    """

    # Other auth policies that extend Pyramid auth policies, e.g.
    # ``Pyramid.authentication.CallbackAuthenticationPolicy``, automatically
    # get a ``userid`` principal via its ``effective_principals`` method.
    # But :py:class:`h.auth.policy.AuthClientPolicy` overrides ``effective_principals``
    # with its own method, so the ``userid`` principal needs to be added explicitly here
    # for forwarded users
    userid_principals = [user.userid]

    user_principals = principals_for_user(user)
    client_principals = principals_for_auth_client(client)
    auth_client_principals = [role.AuthClientUser]

    all_principals = (
        userid_principals + user_principals + client_principals + auth_client_principals
    )
    distinct_principals = list(set(all_principals))

    return distinct_principals
