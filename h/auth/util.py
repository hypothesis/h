# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import base64

from pyramid import security

from h.auth import role
from h._compat import text_type


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
    if authtype.lower() != "basic":
        return None
    try:
        user_pass_bytes = base64.standard_b64decode(value)
    except TypeError:  # failed to decode
        return None
    try:
        # See the lengthy comment in the tests about why we assume UTF-8
        # encoding here.
        user_pass = user_pass_bytes.decode("utf-8")
    except UnicodeError:  # not UTF-8
        return None
    try:
        username, password = user_pass.split(":", 1)
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
    user_service = request.find_service(name="user")
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


def authority(request):
    """
    Return the value of the h.authority config settings.

    Falls back on returning request.domain if h.authority isn't set.
    """
    return text_type(request.registry.settings.get("h.authority", request.domain))
