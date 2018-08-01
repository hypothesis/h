# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import base64

import hmac

import sqlalchemy as sa
from pyramid import security

from h.auth import role
from h._compat import text_type
from h.exceptions import ClientUnauthorized
from h.models.auth_client import GrantType, AuthClient
from h.schemas import ValidationError


def basic_auth_creds(request):
    """
    Extract any HTTP Basic authentication credentials for the request.

    Returns a tuple with the HTTP Basic access authentication credentials
    ``(username, password)`` if provided, otherwise ``None``.

    :param request: the request object
    :type request: pyramid.request.Request

    :returns: a tuple of (username, password) or None
    :rtype: tuple or NoneType
    """
    try:
        authtype, value = request.authorization
    except TypeError:  # no authorization header
        return None
    if authtype.lower() != 'basic':
        return None
    try:
        user_pass_bytes = base64.standard_b64decode(value)
    except TypeError:  # failed to decode
        return None
    try:
        # See the lengthy comment in the tests about why we assume UTF-8
        # encoding here.
        user_pass = user_pass_bytes.decode('utf-8')
    except UnicodeError:  # not UTF-8
        return None
    try:
        username, password = user_pass.split(':', 1)
    except ValueError:  # not enough values to unpack
        return None
    return (username, password)


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
    user_service = request.find_service(name='user')
    user = user_service.fetch(userid)

    return principals_for_user(user)


def principals_for_user(user):
    """Return the list of additional principals for a user, or None."""
    if user is None:
        return None

    principals = set()
    if user.admin:
        principals.add(role.Admin)
    if user.staff:
        principals.add(role.Staff)
    for group in user.groups:
        principals.add('group:{group.pubid}'.format(group=group))
    principals.add('authority:{authority}'.format(authority=user.authority))

    return list(principals)


def translate_annotation_principals(principals):
    """
    Translate a list of annotation principals to a list of pyramid principals.
    """
    result = set([])
    for principal in principals:
        # Ignore suspicious principals from annotations
        if principal.startswith('system.'):
            continue
        if principal == 'group:__world__':
            result.add(security.Everyone)
        else:
            result.add(principal)
    return list(result)


def authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return text_type(request.registry.settings.get('h.authority', request.domain))


def verify_auth_client(client_id, client_secret, db_session):
    """
    Look up ``auth_client`` corresponding to ``client_id`` and ``client_secret``

    Retrieve and return valid auth_client matching credentials or ``None``.

    :param: client_id
    :param: client_secret
    :param: db_session

    :rtype: h.models.AuthClient or None
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


def verify_forwarded_user(client, forwarded_userid, request):
    """
    Fetch user by forwarded_userid and verify its authority matches the client's

    :rtype:`h.models.User` or None
    """
    if client.authority is None:
        return None

    user_service = request.find_service(name='user')
    user = user_service.fetch(forwarded_userid)

    if user and user.authority == client.authority:
        return user

    return None


def check_auth_client(username, password, request):
    """
    Perform authentication for an auth_client client.

    Return list of appropriate principals or None if authentication is
    unsuccessful.

    Validate the basic auth credentials from the request by matching them to
    an auth_client record in the DB.

    If an HTTP `X-Forwarded-User` header is present in the request, this
    represents the intent to authenticate "on behalf of" a user within
    the auth_client's authority. If this header is present, the user indicated
    by its value (a `~h.models.user.User.userid`) _must_ exist and be within
    the auth_client's authority, or authentication will fail.

    This function is intended to be used as a callback for an
    authentication policy

    :param username: username parsed out of Authorization header (Basic)
    :param password: password parsed out of Authorization header (Basic)
    :returns: additional principals for the auth_client or None
    :rtype: list or None
    """
    client_id = username
    client_secret = password

    # validate that the credentials in BasicAuth header
    # match an AuthClient record in the db
    client = verify_auth_client(client_id, client_secret, request.db)

    if client is None:
        return None

    forwarded_userid = request.headers.get('X-Forwarded-User', None)

    if forwarded_userid is None:  # No forwarded user; set principals for basic auth_client
        return principals_for_auth_client(client)

    user = verify_forwarded_user(client, forwarded_userid, request)
    if user is not None:
        return principals_for_auth_client_user(user, client)

    return None


def principals_for_auth_client(client):
    """
    Return the list of additional principals for an auth client

    :type client: h.models.AuthClient
    :rtype: list
    """

    principals = set([])

    principals.add('client:{client_id}@{authority}'.format(client_id=client.id, authority=client.authority))
    principals.add('authority:{authority}'.format(authority=client.authority))

    return list(principals)


def principals_for_auth_client_user(user, client):
    """
    Return a union of client and user principals for forwarded user

    :param user:
    :type user: `h.models.User`
    :param client:
    :type client: `h.models.AuthClient`
    :rtype: list
    """
    user_principals = principals_for_user(user)
    client_principals = principals_for_auth_client(client)

    all_principals = user_principals + client_principals
    distinct_principals = list(set(all_principals))

    return distinct_principals


def request_auth_client(request):
    """
    Locate a matching AuthClient record in the database.

    :param request: the request object
    :type request: pyramid.request.Request

    :returns: an auth client
    :rtype: an AuthClient model

    :raises ClientUnauthorized: if the client does not have a valid Client ID
    and Client Secret or is not allowed to create users in their authority.
    """
    creds = basic_auth_creds(request)
    if creds is None:
        raise ClientUnauthorized()

    # We fetch the client by its ID and then do a constant-time comparison of
    # the secret with that provided in the request.
    #
    # It is important not to include the secret as part of the SQL query
    # because the resulting code may be subject to a timing attack.
    client_id, client_secret = creds
    try:
        client = request.db.query(AuthClient).get(client_id)
    except sa.exc.StatementError:  # client_id is malformed
        raise ClientUnauthorized()
    if client is None:
        raise ClientUnauthorized()
    if client.secret is None:  # client is not confidential
        raise ClientUnauthorized()
    if client.grant_type != GrantType.client_credentials:  # client not allowed to create users
        raise ClientUnauthorized()

    if not hmac.compare_digest(client.secret, client_secret):
        raise ClientUnauthorized()

    return client


def validate_auth_client_authority(client, authority):
    """
    Validate that the auth client authority matches the request authority.
    """
    if client.authority != authority:
        raise ValidationError("'authority' does not match authenticated client")
