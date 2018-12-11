# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime

import newrelic.agent
from zope.interface import implementer

from h._compat import text_type
from h.auth.interfaces import IAuthenticationToken


@implementer(IAuthenticationToken)
class Token(object):
    r"""
    A long-lived API token for a user.

    This is a wrapper class that wraps an ``h.models.Token`` and provides an
    implementation of the ``IAuthenticationToken`` interface.

    Unlike ``models.Token`` this class is not a sqlalchemy ORM class so it can
    be used after the request's db session has been committed or invalidated
    without getting ``DetachedInstanceError``\ s from sqlalchemy.

    """

    def __init__(self, token_model):
        self.expires = token_model.expires
        self.userid = token_model.userid

        # Associates the userid with a given transaction/web request.
        newrelic.agent.add_custom_parameter("userid", self.userid)

    def is_valid(self):
        """Return ``True`` if this token is not expired, ``False`` if it is."""
        if self.expires is None:
            return True
        now = datetime.datetime.utcnow()
        return now < self.expires


def auth_token(request):
    """
    Fetch the token (if any) associated with a request.

    :param request: the request object
    :type request: pyramid.request.Request

    :returns: the auth token carried by the request, or None
    :rtype: h.models.Token or None
    """
    try:
        header = request.headers["Authorization"]
    except KeyError:
        return None

    if not header.startswith("Bearer "):
        return None

    token = text_type(header[len("Bearer ") :]).strip()
    # If the token is empty at this point, it is clearly invalid and we
    # should reject it.
    if not token:
        return None

    return token
