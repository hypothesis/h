# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from zope.interface import Attribute, Interface


class IAuthenticationToken(Interface):
    """Represents an authentication token."""

    userid = Attribute("""The userid to which this token was issued.""")
