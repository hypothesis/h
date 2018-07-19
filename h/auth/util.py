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


def validate_auth_client_authority(client, data):
    """
    Validate that the auth client authority matches the request authority.
    """
    if client.authority != data.get('authority'):
        raise ValidationError("'authority' does not match authenticated client")
